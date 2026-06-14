from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Avg, Count, Q, Case, When, IntegerField, F
from django.utils import timezone
from datetime import timedelta

from .services import (
    safe_service_call, generate_reminders_from_record,
    get_stats_overview, get_care_stats, get_care_method_comfort,
    get_brand_comfort, get_water_content_fit, get_purpose_stats,
    get_comfort_trend, get_eye_tips, generate_restock_suggestions,
    get_budget_stats, get_budget_monthly_summary,
    calculate_travel_risk_level, generate_travel_suggestions_and_risks,
    get_travel_plan_stats, update_travel_auto_status, get_outfit_plan_stats
)

from .models import (
    Lens, WearRecord, CareRecord, CareReminder, OutfitPlan, PurchaseRecord, RestockSuggestion,
    TravelPlan, TravelLensItem, TravelSupplyItem, TravelDailyPlan, TravelRiskAlert
)
from .serializers import (
    LensSerializer, WearRecordSerializer,
    CareRecordSerializer, CareReminderSerializer,
    OutfitPlanSerializer, OutfitPlanStatsSerializer,
    PurchaseRecordSerializer, RestockSuggestionSerializer,
    BudgetStatsSerializer,
    TravelPlanSerializer, TravelLensItemSerializer, TravelSupplyItemSerializer,
    TravelDailyPlanSerializer, TravelRiskAlertSerializer, TravelStatsSerializer
)


class LensViewSet(viewsets.ModelViewSet):
    queryset = Lens.objects.all()
    serializer_class = LensSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        purpose_filter = self.request.query_params.get('purpose')
        brand_filter = self.request.query_params.get('brand')
        care_status_filter = self.request.query_params.get('care_status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if purpose_filter:
            qs = qs.filter(purpose=purpose_filter)
        if brand_filter:
            qs = qs.filter(brand__icontains=brand_filter)
        if care_status_filter:
            today = timezone.now().date()
            future_3 = today + timedelta(days=3)
            future_7 = today + timedelta(days=7)
            if care_status_filter == 'normal':
                rest_q = Q(need_rest_observation=True) & (Q(rest_until_date__gte=today) | Q(rest_until_date__isnull=True))
                overdue_q = Q(next_care_date__lt=today) | Q(next_checkup_date__lt=today)
                soon_q = (Q(next_care_date__lte=future_3) & Q(next_care_date__gte=today)) | \
                         (Q(next_checkup_date__lte=future_7) & Q(next_checkup_date__gte=today))
                qs = qs.exclude(rest_q | overdue_q | soon_q)
                pks = [lens.pk for lens in qs if lens.get_care_status() == 'normal']
                qs = qs.filter(pk__in=pks)
            elif care_status_filter == 'rest':
                qs = qs.filter(
                    Q(need_rest_observation=True) &
                    (Q(rest_until_date__gte=today) | Q(rest_until_date__isnull=True))
                )
            elif care_status_filter == 'overdue':
                qs = qs.filter(
                    Q(next_care_date__lt=today) | Q(next_checkup_date__lt=today)
                )
            elif care_status_filter == 'soon':
                qs = qs.filter(
                    Q(next_care_date__lte=future_3, next_care_date__gte=today) |
                    Q(next_checkup_date__lte=future_7, next_checkup_date__gte=today)
                )
        return qs

    @action(detail=False, methods=['get'])
    def expiring(self, request):
        today = timezone.now().date()
        threshold_days = int(request.query_params.get('days', 30))
        future_date = today + timedelta(days=threshold_days)
        lenses = Lens.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=future_date
        ).exclude(status='used_up')
        already_expired = Lens.objects.filter(expiry_date__lt=today).exclude(status='expired')
        all_expiring = list(lenses) + list(already_expired)
        for lens in all_expiring:
            records = WearRecord.objects.filter(lens=lens)
            total_hours = records.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
            lens.total_wear_hours = round(total_hours, 1)
        serializer = self.get_serializer(all_expiring, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unused(self, request):
        today = timezone.now().date()
        days_threshold = int(request.query_params.get('days', 90))
        cutoff_date = today - timedelta(days=days_threshold)
        lenses = Lens.objects.exclude(status='used_up').exclude(status='expired')
        unused_lenses = []
        for lens in lenses:
            last_record = WearRecord.objects.filter(lens=lens).order_by('-wear_date').first()
            if last_record:
                if last_record.wear_date < cutoff_date:
                    records = WearRecord.objects.filter(lens=lens)
                    total_hours = records.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
                    lens.total_wear_hours = round(total_hours, 1)
                    lens.last_wear_date = last_record.wear_date
                    unused_lenses.append(lens)
            else:
                if lens.created_at.date() < cutoff_date:
                    lens.total_wear_hours = 0
                    lens.last_wear_date = None
                    unused_lenses.append(lens)
        serializer = self.get_serializer(unused_lenses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def care_warnings(self, request):
        today = timezone.now().date()
        lenses = Lens.objects.exclude(status__in=['used_up', 'expired'])
        result = []
        for lens in lenses:
            care_status = lens.get_care_status()
            if care_status != 'normal':
                result.append(lens)
        serializer = self.get_serializer(result, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def open(self, request, pk=None):
        lens = self.get_object()
        lens.status = 'opened'
        if not lens.open_date:
            lens.open_date = timezone.now().date()
        lens.save()
        return Response({'status': 'opened'})

    @action(detail=True, methods=['post'])
    def mark_used_up(self, request, pk=None):
        lens = self.get_object()
        lens.status = 'used_up'
        lens.save()
        return Response({'status': 'used_up'})

    @action(detail=True, methods=['post'])
    def mark_care_done(self, request, pk=None):
        lens = self.get_object()
        notes = request.data.get('notes', '')
        next_date = request.data.get('next_care_date')
        CareRecord.objects.create(
            lens=lens,
            care_type='routine',
            care_date=timezone.now().date(),
            notes=notes
        )
        if next_date:
            lens.next_care_date = next_date
        else:
            lens.next_care_date = timezone.now().date() + timedelta(days=7)
        lens.save()
        return Response({'status': 'success', 'next_care_date': lens.next_care_date.isoformat()})

    @action(detail=True, methods=['post'])
    def mark_checkup_done(self, request, pk=None):
        lens = self.get_object()
        notes = request.data.get('notes', '')
        next_date = request.data.get('next_checkup_date')
        CareRecord.objects.create(
            lens=lens,
            care_type='checkup',
            care_date=timezone.now().date(),
            notes=notes
        )
        if next_date:
            lens.next_checkup_date = next_date
        else:
            lens.next_checkup_date = timezone.now().date() + timedelta(days=180)
        lens.save()
        return Response({'status': 'success', 'next_checkup_date': lens.next_checkup_date.isoformat()})

    @action(detail=True, methods=['post'])
    def start_rest(self, request, pk=None):
        lens = self.get_object()
        days = int(request.data.get('days', 3))
        notes = request.data.get('notes', '')
        lens.need_rest_observation = True
        lens.rest_until_date = timezone.now().date() + timedelta(days=days)
        lens.save()
        CareRecord.objects.create(
            lens=lens,
            care_type='rest_start',
            care_date=timezone.now().date(),
            notes=notes or f'建议停戴 {days} 天'
        )
        return Response({
            'status': 'rest_started',
            'rest_until_date': lens.rest_until_date.isoformat()
        })

    @action(detail=True, methods=['post'])
    def end_rest(self, request, pk=None):
        lens = self.get_object()
        notes = request.data.get('notes', '')
        lens.need_rest_observation = False
        lens.rest_until_date = None
        lens.save()
        CareRecord.objects.create(
            lens=lens,
            care_type='rest_end',
            care_date=timezone.now().date(),
            notes=notes or '停戴观察结束'
        )
        return Response({'status': 'rest_ended'})

    @action(detail=True, methods=['get'])
    def care_records(self, request, pk=None):
        lens = self.get_object()
        records = lens.care_records.all()
        serializer = CareRecordSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reminders(self, request, pk=None):
        lens = self.get_object()
        include_dismissed = request.query_params.get('include_dismissed', 'false') == 'true'
        if include_dismissed:
            reminders = lens.reminders.all()
        else:
            reminders = lens.reminders.filter(is_dismissed=False)
        serializer = CareReminderSerializer(reminders, many=True)
        return Response(serializer.data)


class WearRecordViewSet(viewsets.ModelViewSet):
    queryset = WearRecord.objects.all()
    serializer_class = WearRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        lens_id = self.request.query_params.get('lens_id')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if lens_id:
            qs = qs.filter(lens_id=lens_id)
        if date_from:
            qs = qs.filter(wear_date__gte=date_from)
        if date_to:
            qs = qs.filter(wear_date__lte=date_to)
        return qs

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            record = WearRecord.objects.get(pk=response.data['id'])
            reminders = generate_reminders_from_record(record)
            reminder_serializer = CareReminderSerializer(reminders, many=True)
            response.data['generated_reminders'] = reminder_serializer.data
        return response

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        reminders = generate_reminders_from_record(instance)
        reminder_serializer = CareReminderSerializer(reminders, many=True)
        data = serializer.data
        data['generated_reminders'] = reminder_serializer.data
        return Response(data)

    @action(detail=False, methods=['get'])
    def daily_totals(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        qs = WearRecord.objects.all()
        if date_from:
            qs = qs.filter(wear_date__gte=date_from)
        if date_to:
            qs = qs.filter(wear_date__lte=date_to)
        daily_map = {}
        for r in qs:
            d = r.wear_date.isoformat()
            if d not in daily_map:
                daily_map[d] = {'date': d, 'hours': 0, 'count': 0, 'comfort_sum': 0}
            daily_map[d]['hours'] += r.duration_hours
            daily_map[d]['count'] += 1
            daily_map[d]['comfort_sum'] += r.comfort_level
        result = []
        for d, v in sorted(daily_map.items(), key=lambda x: x[0], reverse=True):
            result.append({
                'date': v['date'],
                'total_hours': round(v['hours'], 2),
                'count': v['count'],
                'avg_comfort': round(v['comfort_sum'] / v['count'], 2) if v['count'] else 0
            })
        return Response(result)

    @action(detail=False, methods=['get'])
    def today_warning(self, request):
        today = timezone.now().date()
        today_records = WearRecord.objects.filter(wear_date=today)
        total_hours = today_records.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
        warning_threshold = 8
        max_threshold = 12
        status_level = 'normal'
        message = ''
        if total_hours >= max_threshold:
            status_level = 'danger'
            message = f'今日已佩戴 {total_hours:.1f} 小时，严重超时！建议立即取下镜片休息。'
        elif total_hours >= warning_threshold:
            status_level = 'warning'
            message = f'今日已佩戴 {total_hours:.1f} 小时，接近建议上限（8小时），请适时取下休息。'
        else:
            message = f'今日已佩戴 {total_hours:.1f} 小时，状态良好。建议单日不超过8小时。'
        return Response({
            'total_hours': round(total_hours, 1),
            'status': status_level,
            'message': message,
            'warning_threshold': warning_threshold,
            'max_threshold': max_threshold,
            'record_count': today_records.count()
        })


class CareRecordViewSet(viewsets.ModelViewSet):
    queryset = CareRecord.objects.all()
    serializer_class = CareRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        lens_id = self.request.query_params.get('lens_id')
        care_type = self.request.query_params.get('care_type')
        if lens_id:
            qs = qs.filter(lens_id=lens_id)
        if care_type:
            qs = qs.filter(care_type=care_type)
        return qs


class CareReminderViewSet(viewsets.ModelViewSet):
    queryset = CareReminder.objects.all()
    serializer_class = CareReminderSerializer
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        lens_id = self.request.query_params.get('lens_id')
        reminder_type = self.request.query_params.get('reminder_type')
        severity = self.request.query_params.get('severity')
        include_dismissed = self.request.query_params.get('include_dismissed', 'false') == 'true'
        if lens_id:
            qs = qs.filter(lens_id=lens_id)
        if reminder_type:
            qs = qs.filter(reminder_type=reminder_type)
        if severity:
            qs = qs.filter(severity=severity)
        if not include_dismissed:
            qs = qs.filter(is_dismissed=False)
        return qs

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        reminder = self.get_object()
        reminder.is_read = True
        reminder.save()
        return Response({'status': 'read'})

    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        reminder = self.get_object()
        reminder.is_dismissed = True
        reminder.save()
        return Response({'status': 'dismissed'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        CareReminder.objects.filter(is_read=False).update(is_read=True)
        return Response({'status': 'all_read'})

    @action(detail=False, methods=['get'])
    def active(self, request):
        today = timezone.now().date()
        reminders = CareReminder.objects.filter(is_dismissed=False).order_by('-severity', '-created_at')
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generate_all(self, request):
        all_reminders = []
        records = WearRecord.objects.filter(wear_date=timezone.now().date())
        for record in records:
            r = generate_reminders_from_record(record)
            all_reminders.extend(r)
        serializer = self.get_serializer(all_reminders, many=True)
        return Response({'count': len(all_reminders), 'reminders': serializer.data})


class StatsViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['get'])
    def overview(self, request):
        try:
            data = get_stats_overview()
        except Exception:
            data = {}
        return Response(data)

    @action(detail=False, methods=['get'])
    def care_stats(self, request):
        try:
            data = get_care_stats()
        except Exception:
            data = {}
        return Response(data)

    @action(detail=False, methods=['get'])
    def care_method_comfort(self, request):
        try:
            data = get_care_method_comfort()
        except Exception:
            data = []
        return Response(data)

    @action(detail=False, methods=['get'])
    def brand_comfort(self, request):
        try:
            data = get_brand_comfort()
        except Exception:
            data = []
        return Response(data)

    @action(detail=False, methods=['get'])
    def water_content_fit(self, request):
        try:
            data = get_water_content_fit()
        except Exception:
            data = []
        return Response(data)

    @action(detail=False, methods=['get'])
    def purpose_stats(self, request):
        try:
            data = get_purpose_stats()
        except Exception:
            data = []
        return Response(data)

    @action(detail=False, methods=['get'])
    def comfort_trend(self, request):
        try:
            days = int(request.query_params.get('days', 30))
            data = get_comfort_trend(days=days)
        except Exception:
            data = []
        return Response(data)

    @action(detail=False, methods=['get'])
    def eye_tips(self, request):
        try:
            data = get_eye_tips()
        except Exception:
            data = []
        return Response(data)


class OutfitPlanViewSet(viewsets.ModelViewSet):
    queryset = OutfitPlan.objects.all()
    serializer_class = OutfitPlanSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        lens_id = self.request.query_params.get('lens_id')
        status = self.request.query_params.get('status')
        scene = self.request.query_params.get('scene')
        makeup_style = self.request.query_params.get('makeup_style')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        expected_date = self.request.query_params.get('expected_date')
        has_tags = self.request.query_params.get('has_tags')

        if lens_id:
            qs = qs.filter(Q(lens_id=lens_id) | Q(backup_lens_id=lens_id))
        if status:
            qs = qs.filter(status=status)
        if scene:
            qs = qs.filter(scene_name=scene)
        if makeup_style:
            qs = qs.filter(makeup_style=makeup_style)
        if date_from:
            qs = qs.filter(expected_wear_date__gte=date_from)
        if date_to:
            qs = qs.filter(expected_wear_date__lte=date_to)
        if expected_date:
            qs = qs.filter(expected_wear_date=expected_date)
        if has_tags:
            tags = has_tags.split(',')
            for tag in tags:
                qs = qs.filter(tags__contains=tag)
        return qs

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        plan = self.get_object()
        wear_record_id = request.data.get('wear_record_id')
        wear_record = None

        if wear_record_id:
            try:
                wear_record = WearRecord.objects.get(pk=wear_record_id)
                existing_plan = OutfitPlan.objects.filter(wear_record=wear_record).exclude(pk=plan.pk).first()
                if existing_plan:
                    return Response(
                        {'error': f'该佩戴记录已被「{existing_plan.get_scene_name_display()}」方案使用，无法重复关联'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except WearRecord.DoesNotExist:
                pass

        plan.mark_as_completed(wear_record=wear_record)
        serializer = self.get_serializer(plan)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_cancelled(self, request, pk=None):
        plan = self.get_object()
        plan.status = 'cancelled'
        plan.save()
        serializer = self.get_serializer(plan)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def link_record(self, request, pk=None):
        plan = self.get_object()
        wear_record_id = request.data.get('wear_record_id')
        if not wear_record_id:
            return Response({'error': '请选择佩戴记录'}, status=status.HTTP_400_BAD_REQUEST)

        if plan.status != 'completed':
            return Response({'error': '只有已执行的计划才能关联佩戴记录'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wear_record = WearRecord.objects.get(pk=wear_record_id)
        except WearRecord.DoesNotExist:
            return Response({'error': '佩戴记录不存在'}, status=status.HTTP_404_NOT_FOUND)

        existing_plan = OutfitPlan.objects.filter(wear_record=wear_record).exclude(pk=plan.pk).first()
        if existing_plan:
            return Response(
                {'error': f'该佩戴记录已被「{existing_plan.get_scene_name_display()}」方案使用，无法重复关联'},
                status=status.HTTP_400_BAD_REQUEST
            )

        plan.wear_record = wear_record
        plan.update_tags()
        plan.save()
        serializer = self.get_serializer(plan)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unlink_record(self, request, pk=None):
        plan = self.get_object()
        plan.wear_record = None
        plan.tags = []
        plan.save()
        serializer = self.get_serializer(plan)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        today = timezone.now().date()
        days = int(request.query_params.get('days', 7))
        end_date = today + timedelta(days=days)
        plans = OutfitPlan.objects.filter(
            status='pending',
            expected_wear_date__gte=today,
            expected_wear_date__lte=end_date
        ).order_by('expected_wear_date', 'created_at')
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        today = timezone.now().date()
        plans = OutfitPlan.objects.filter(
            status='pending',
            expected_wear_date__lt=today
        ).order_by('-expected_wear_date')
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        date = request.query_params.get('date')
        if not date:
            return Response({'error': 'date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        plans = OutfitPlan.objects.filter(expected_wear_date=date).order_by('created_at')
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        qs = OutfitPlan.objects.all()
        if date_from:
            qs = qs.filter(expected_wear_date__gte=date_from)
        if date_to:
            qs = qs.filter(expected_wear_date__lte=date_to)

        calendar_data = {}
        for plan in qs:
            date_str = plan.expected_wear_date.isoformat()
            if date_str not in calendar_data:
                calendar_data[date_str] = []
            calendar_data[date_str].append({
                'id': plan.id,
                'scene_name': plan.get_scene_display_name(),
                'status': plan.status,
                'lens_brand': plan.lens.brand if plan.lens else '',
                'match_score': plan.match_score
            })
        return Response(calendar_data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        try:
            data = get_outfit_plan_stats()
        except Exception:
            data = {}
        serializer = OutfitPlanStatsSerializer(data)
        return Response(serializer.data)


class PurchaseRecordViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRecord.objects.all()
    serializer_class = PurchaseRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        lens_id = self.request.query_params.get('lens_id')
        brand = self.request.query_params.get('brand')
        channel = self.request.query_params.get('channel')
        budget_month = self.request.query_params.get('budget_month')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        payment_status = self.request.query_params.get('payment_status')
        restock_priority = self.request.query_params.get('restock_priority')

        if lens_id:
            qs = qs.filter(lens_id=lens_id)
        if brand:
            qs = qs.filter(lens__brand__icontains=brand)
        if channel:
            qs = qs.filter(Q(purchase_channel=channel) | Q(custom_channel__icontains=channel))
        if budget_month:
            qs = qs.filter(budget_month=budget_month)
        if date_from:
            qs = qs.filter(purchase_date__gte=date_from)
        if date_to:
            qs = qs.filter(purchase_date__lte=date_to)
        if payment_status:
            qs = qs.filter(payment_status=payment_status)
        if restock_priority:
            qs = qs.filter(lens__restock_priority=restock_priority)
        return qs

    @action(detail=False, methods=['get'])
    def by_month(self, request):
        month = request.query_params.get('month')
        if not month:
            return Response({'error': 'month parameter is required (YYYY-MM)'}, status=400)
        records = self.get_queryset().filter(budget_month=month)
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def months(self, request):
        months = PurchaseRecord.objects.values_list('budget_month', flat=True).distinct().order_by('-budget_month')
        return Response(list(months))

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.lens:
            instance.lens.stock_quantity = max(0, instance.lens.stock_quantity - instance.quantity)
            instance.lens.save()
        return super().destroy(request, *args, **kwargs)


class RestockSuggestionViewSet(viewsets.ModelViewSet):
    queryset = RestockSuggestion.objects.all()
    serializer_class = RestockSuggestionSerializer
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        lens_id = self.request.query_params.get('lens_id')
        suggestion_type = self.request.query_params.get('suggestion_type')
        severity = self.request.query_params.get('severity')
        include_dismissed = self.request.query_params.get('include_dismissed', 'false') == 'true'
        include_action_taken = self.request.query_params.get('include_action_taken', 'false') == 'true'

        if lens_id:
            qs = qs.filter(lens_id=lens_id)
        if suggestion_type:
            qs = qs.filter(suggestion_type=suggestion_type)
        if severity:
            qs = qs.filter(severity=severity)
        if not include_dismissed:
            qs = qs.filter(is_dismissed=False)
        if not include_action_taken:
            qs = qs.filter(is_action_taken=False)
        return qs

    @action(detail=False, methods=['post'])
    def generate(self, request):
        suggestions = generate_restock_suggestions()
        serializer = self.get_serializer(suggestions, many=True)
        return Response({'count': len(suggestions), 'suggestions': serializer.data})

    @action(detail=False, methods=['get'])
    def active(self, request):
        suggestions = self.get_queryset().order_by('-severity', '-triggered_at')
        serializer = self.get_serializer(suggestions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_action_taken(self, request, pk=None):
        suggestion = self.get_object()
        suggestion.is_action_taken = True
        suggestion.action_taken_at = timezone.now()
        suggestion.action_notes = request.data.get('notes', '')
        suggestion.save()
        return Response({'status': 'action_taken'})

    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        suggestion = self.get_object()
        suggestion.is_dismissed = True
        suggestion.save()
        return Response({'status': 'dismissed'})

    @action(detail=False, methods=['post'])
    def mark_all_action_taken(self, request):
        RestockSuggestion.objects.filter(is_action_taken=False).update(
            is_action_taken=True,
            action_taken_at=timezone.now()
        )
        return Response({'status': 'all_action_taken'})

    @action(detail=False, methods=['post'])
    def dismiss_all(self, request):
        RestockSuggestion.objects.filter(is_dismissed=False).update(is_dismissed=True)
        return Response({'status': 'all_dismissed'})


class BudgetViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['get'])
    def stats(self, request):
        try:
            today = timezone.now().date()
            budget_month = request.query_params.get('month', today.strftime('%Y-%m'))
            budget_limit = float(request.query_params.get('limit', 500))
            data = get_budget_stats(budget_month=budget_month, budget_limit=budget_limit)
        except Exception:
            data = {}
        serializer = BudgetStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        try:
            data = get_budget_monthly_summary()
        except Exception:
            data = []
        return Response(data)


class TravelPlanViewSet(viewsets.ModelViewSet):
    queryset = TravelPlan.objects.all()
    serializer_class = TravelPlanSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        for plan in qs:
            update_travel_auto_status(plan)

        status = self.request.query_params.get('status')
        risk_level = self.request.query_params.get('risk_level')
        destination = self.request.query_params.get('destination')
        month = self.request.query_params.get('month')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        lens_id = self.request.query_params.get('lens_id')

        if status:
            statuses = status.split(',')
            qs = qs.filter(status__in=statuses)
        if risk_level:
            qs = qs.filter(risk_level=risk_level)
        if destination:
            qs = qs.filter(destination__icontains=destination)
        if month:
            qs = qs.filter(Q(start_date__startswith=month) | Q(end_date__startswith=month))
        if date_from:
            qs = qs.filter(start_date__gte=date_from)
        if date_to:
            qs = qs.filter(end_date__lte=date_to)
        if lens_id:
            qs = qs.filter(
                Q(lens_items__lens_id=lens_id) | Q(daily_plans__expected_wear_lens_id=lens_id)
            ).distinct()
        return qs

    def perform_create(self, serializer):
        instance = serializer.save()
        calculate_travel_risk_level(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        calculate_travel_risk_level(instance)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        today = timezone.now().date()
        days = int(request.query_params.get('days', 30))
        end_date = today + timedelta(days=days)
        plans = self.get_queryset().filter(
            status__in=['planning', 'upcoming', 'in_progress'],
            start_date__lte=end_date
        ).order_by('start_date')
        for plan in plans:
            calculate_travel_risk_level(plan)
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def in_progress(self, request):
        today = timezone.now().date()
        plans = self.get_queryset().filter(
            start_date__lte=today,
            end_date__gte=today
        ).order_by('start_date')
        for plan in plans:
            calculate_travel_risk_level(plan)
        serializer = self.get_serializer(plans, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def suggestions(self, request, pk=None):
        plan = self.get_object()
        try:
            suggestions, risks = generate_travel_suggestions_and_risks(plan)
        except Exception:
            suggestions, risks = [], []
        try:
            risk_level = calculate_travel_risk_level(plan)
        except Exception:
            risk_level = 'low'
        return Response({
            'suggestions': suggestions,
            'risks': risks,
            'risk_level': risk_level
        })

    @action(detail=True, methods=['post'])
    def recalculate_risk(self, request, pk=None):
        plan = self.get_object()
        risk_level = calculate_travel_risk_level(plan)
        return Response({'risk_level': risk_level})

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        plan = self.get_object()
        plan.status = 'completed'
        plan.save()
        serializer = self.get_serializer(plan)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_cancelled(self, request, pk=None):
        plan = self.get_object()
        plan.status = 'cancelled'
        plan.save()
        serializer = self.get_serializer(plan)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def generate_alerts(self, request, pk=None):
        plan = self.get_object()
        try:
            suggestions, risks = generate_travel_suggestions_and_risks(plan)
        except Exception:
            suggestions, risks = [], []
        created_alerts = []
        for risk in risks:
            alert_type = risk.get('type', 'other')
            valid_types = [t[0] for t in TravelRiskAlert.ALERT_TYPE_CHOICES]
            if alert_type not in valid_types:
                alert_type = 'other'
            exists = TravelRiskAlert.objects.filter(
                travel_plan=plan,
                title=risk.get('title', ''),
                is_dismissed=False
            ).exists()
            if not exists:
                alert = TravelRiskAlert.objects.create(
                    travel_plan=plan,
                    alert_type=alert_type,
                    severity=risk.get('level', 'info'),
                    title=risk.get('title', ''),
                    message=risk.get('message', ''),
                    related_lens_id=risk.get('lens_id')
                )
                created_alerts.append(alert)
        serializer = TravelRiskAlertSerializer(created_alerts, many=True)
        return Response({'count': len(created_alerts), 'alerts': serializer.data})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        try:
            data = get_travel_plan_stats()
        except Exception:
            data = {}
        serializer = TravelStatsSerializer(data)
        return Response(serializer.data)


class TravelLensItemViewSet(viewsets.ModelViewSet):
    queryset = TravelLensItem.objects.all()
    serializer_class = TravelLensItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        travel_plan_id = self.request.query_params.get('travel_plan_id')
        lens_id = self.request.query_params.get('lens_id')
        role = self.request.query_params.get('role')
        if travel_plan_id:
            qs = qs.filter(travel_plan_id=travel_plan_id)
        if lens_id:
            qs = qs.filter(lens_id=lens_id)
        if role:
            qs = qs.filter(role=role)
        return qs


class TravelSupplyItemViewSet(viewsets.ModelViewSet):
    queryset = TravelSupplyItem.objects.all()
    serializer_class = TravelSupplyItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        travel_plan_id = self.request.query_params.get('travel_plan_id')
        supply_type = self.request.query_params.get('supply_type')
        is_checked = self.request.query_params.get('is_checked')
        if travel_plan_id:
            qs = qs.filter(travel_plan_id=travel_plan_id)
        if supply_type:
            qs = qs.filter(supply_type=supply_type)
        if is_checked is not None:
            qs = qs.filter(is_checked=(is_checked == 'true'))
        return qs

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        item = self.get_object()
        item.is_checked = not item.is_checked
        item.save()
        if item.travel_plan:
            calculate_travel_risk_level(item.travel_plan)
        serializer = self.get_serializer(item)
        return Response(serializer.data)


class TravelDailyPlanViewSet(viewsets.ModelViewSet):
    queryset = TravelDailyPlan.objects.all()
    serializer_class = TravelDailyPlanSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        travel_plan_id = self.request.query_params.get('travel_plan_id')
        lens_id = self.request.query_params.get('lens_id')
        date = self.request.query_params.get('date')
        if travel_plan_id:
            qs = qs.filter(travel_plan_id=travel_plan_id)
        if lens_id:
            qs = qs.filter(expected_wear_lens_id=lens_id)
        if date:
            qs = qs.filter(plan_date=date)
        return qs


class TravelRiskAlertViewSet(viewsets.ModelViewSet):
    queryset = TravelRiskAlert.objects.all()
    serializer_class = TravelRiskAlertSerializer
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        travel_plan_id = self.request.query_params.get('travel_plan_id')
        alert_type = self.request.query_params.get('alert_type')
        severity = self.request.query_params.get('severity')
        include_dismissed = self.request.query_params.get('include_dismissed', 'false') == 'true'
        if travel_plan_id:
            qs = qs.filter(travel_plan_id=travel_plan_id)
        if alert_type:
            qs = qs.filter(alert_type=alert_type)
        if severity:
            qs = qs.filter(severity=severity)
        if not include_dismissed:
            qs = qs.filter(is_dismissed=False)
        return qs

    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        alert = self.get_object()
        alert.is_dismissed = True
        alert.save()
        return Response({'status': 'dismissed'})

    @action(detail=False, methods=['get'])
    def active(self, request):
        today = timezone.now().date()
        alerts = self.get_queryset().filter(
            travel_plan__end_date__gte=today - timedelta(days=7)
        ).order_by('-severity', '-created_at')
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
