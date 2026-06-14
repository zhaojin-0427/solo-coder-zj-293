from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Avg, Count, Q, Case, When, IntegerField, F
from django.utils import timezone
from datetime import timedelta

from .models import Lens, WearRecord, CareRecord, CareReminder, OutfitPlan
from .serializers import (
    LensSerializer, WearRecordSerializer,
    CareRecordSerializer, CareReminderSerializer,
    OutfitPlanSerializer, OutfitPlanStatsSerializer
)


def generate_reminders_from_record(record):
    if not record.lens:
        return []

    lens = record.lens
    today = record.wear_date
    reminders = []

    today_records = WearRecord.objects.filter(lens=lens, wear_date=today)
    total_hours_today = sum(r.duration_hours for r in today_records)

    lens_daily_limit = lens.daily_wear_limit()
    if total_hours_today >= 12:
        reminders.append({
            'lens': lens,
            'reminder_type': 'risk',
            'severity': 'danger',
            'title': '单日佩戴严重超时',
            'message': f'今日已佩戴 {total_hours_today:.1f} 小时，远超建议上限（{lens_daily_limit}h）。建议立即取下镜片，让眼睛充分休息，至少间隔24小时再佩戴。',
            'target_date': today,
            'triggered_by_record': record,
        })
    elif total_hours_today >= lens_daily_limit + 2:
        reminders.append({
            'lens': lens,
            'reminder_type': 'risk',
            'severity': 'warning',
            'title': '单日佩戴时长偏长',
            'message': f'今日已佩戴 {total_hours_today:.1f} 小时，超过建议上限（{lens_daily_limit}h）。建议取下镜片休息，明日减少佩戴时长。',
            'target_date': today,
            'triggered_by_record': record,
        })

    if record.comfort_level <= 2:
        reminders.append({
            'lens': lens,
            'reminder_type': 'risk',
            'severity': 'warning',
            'title': '舒适度偏低',
            'message': f'本次佩戴舒适度仅 {record.comfort_level} 分（满分5分）。建议检查镜片是否有破损、沉淀物，或考虑更换护理液/镜片品牌。如持续不适请停戴并就医。',
            'target_date': today,
            'triggered_by_record': record,
        })

    if record.comfort_level <= 1:
        reminders.append({
            'lens': lens,
            'reminder_type': 'rest',
            'severity': 'danger',
            'title': '强烈建议停戴观察',
            'message': '舒适度极低，建议立即停戴此镜片至少3天。如停戴后仍有不适，请及时前往眼科就诊。',
            'target_date': today + timedelta(days=3),
            'triggered_by_record': record,
        })

    bad_reactions = ['redness', 'dryness_redness', 'redness_fatigue', 'all']
    if record.eye_reaction in bad_reactions:
        reminders.append({
            'lens': lens,
            'reminder_type': 'rest',
            'severity': 'danger',
            'title': '眼部出现充血，建议停戴',
            'message': '本次佩戴出现眼部红血丝反应，建议停戴此镜片至少2天。可使用人工泪液缓解，如症状未消退请及时就医。',
            'target_date': today + timedelta(days=2),
            'triggered_by_record': record,
        })

    moderate_reactions = ['dryness', 'fatigue', 'dryness_fatigue']
    if record.eye_reaction in moderate_reactions:
        reminders.append({
            'lens': lens,
            'reminder_type': 'care',
            'severity': 'warning',
            'title': '眼部有轻度不适',
            'message': '本次佩戴出现干涩/视疲劳，建议加强镜片护理，可考虑深度清洁或更换护理液。明日减少佩戴时长。',
            'target_date': today,
            'triggered_by_record': record,
        })

    if lens.open_date:
        days_open = (today - lens.open_date).days
        if lens.replacement_days_after_open and days_open >= lens.replacement_days_after_open:
            reminders.append({
                'lens': lens,
                'reminder_type': 'replacement',
                'severity': 'danger',
                'title': '镜片已超过建议更换周期',
                'message': f'此镜片已开封 {days_open} 天，超过建议更换周期（{lens.replacement_days_after_open}天）。为了眼部健康，请立即更换新镜片。',
                'target_date': lens.open_date + timedelta(days=lens.replacement_days_after_open),
                'triggered_by_record': record,
            })
        elif lens.replacement_days_after_open and days_open >= lens.replacement_days_after_open - 3:
            reminders.append({
                'lens': lens,
                'reminder_type': 'replacement',
                'severity': 'warning',
                'title': '镜片即将达到更换周期',
                'message': f'此镜片已开封 {days_open} 天，距离建议更换周期（{lens.replacement_days_after_open}天）仅剩 {lens.replacement_days_after_open - days_open} 天，请提前准备新镜片。',
                'target_date': lens.open_date + timedelta(days=lens.replacement_days_after_open),
                'triggered_by_record': record,
            })

    if lens.next_care_date and today >= lens.next_care_date:
        reminders.append({
            'lens': lens,
            'reminder_type': 'care',
            'severity': 'warning',
            'title': '请及时护理镜片',
            'message': f'已到达计划护理日期（{lens.next_care_date.isoformat()}），请对镜片进行清洁护理，并更新下次护理日期。',
            'target_date': lens.next_care_date,
            'triggered_by_record': record,
        })

    if lens.next_checkup_date and today >= lens.next_checkup_date:
        reminders.append({
            'lens': lens,
            'reminder_type': 'checkup',
            'severity': 'warning',
            'title': '请及时进行眼科复查',
            'message': f'已到达计划复查日期（{lens.next_checkup_date.isoformat()}），请预约眼科医生进行眼部健康检查。',
            'target_date': lens.next_checkup_date,
            'triggered_by_record': record,
        })

    created_reminders = []
    for rem_data in reminders:
        exists = CareReminder.objects.filter(
            lens=rem_data['lens'],
            reminder_type=rem_data['reminder_type'],
            title=rem_data['title'],
            created_at__date=today
        ).exists()
        if not exists:
            reminder = CareReminder.objects.create(**rem_data)
            created_reminders.append(reminder)

    return created_reminders


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
        today = timezone.now().date()
        total_lenses = Lens.objects.count()
        active_lenses = Lens.objects.exclude(status='used_up').count()
        total_records = WearRecord.objects.count()
        total_hours = WearRecord.objects.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
        avg_comfort = WearRecord.objects.aggregate(Avg('comfort_level'))['comfort_level__avg'] or 0
        expiring_count = Lens.objects.filter(
            expiry_date__lte=today + timedelta(days=30),
            expiry_date__gte=today
        ).exclude(status='used_up').count()
        expired_count = Lens.objects.filter(expiry_date__lt=today).exclude(status='expired').count()

        active_lenses_qs = Lens.objects.exclude(status__in=['used_up', 'expired'])
        care_overdue = active_lenses_qs.filter(
            Q(next_care_date__lt=today) | Q(next_checkup_date__lt=today)
        ).count()
        care_soon = active_lenses_qs.filter(
            Q(next_care_date__lte=today + timedelta(days=3), next_care_date__gte=today) |
            Q(next_checkup_date__lte=today + timedelta(days=7), next_checkup_date__gte=today)
        ).count()
        rest_count = active_lenses_qs.filter(need_rest_observation=True).count()
        checkup_overdue = active_lenses_qs.filter(next_checkup_date__lt=today).count()

        return Response({
            'total_lenses': total_lenses,
            'active_lenses': active_lenses,
            'total_records': total_records,
            'total_hours': round(total_hours, 1),
            'avg_comfort': round(avg_comfort, 1),
            'expiring_count': expiring_count,
            'expired_count': expired_count,
            'care_overdue_count': care_overdue,
            'care_soon_count': care_soon,
            'rest_count': rest_count,
            'checkup_overdue_count': checkup_overdue,
        })

    @action(detail=False, methods=['get'])
    def care_stats(self, request):
        today = timezone.now().date()
        total_care_records = CareRecord.objects.count()
        routine_count = CareRecord.objects.filter(care_type='routine').count()
        checkup_count = CareRecord.objects.filter(care_type='checkup').count()
        rest_count = CareRecord.objects.filter(care_type__in=['rest_start', 'rest_end']).count()

        active_lenses = Lens.objects.exclude(status__in=['used_up', 'expired'])
        with_care_plan = active_lenses.filter(next_care_date__isnull=False).count()
        lenses_with_checkup = active_lenses.filter(next_checkup_date__isnull=False).count()

        recent_30 = today - timedelta(days=30)
        care_in_30 = CareRecord.objects.filter(
            care_type__in=['routine', 'deep_clean'],
            care_date__gte=recent_30
        ).count()

        planned_care_30 = active_lenses.filter(next_care_date__isnull=False).count()
        care_execution_rate = 0
        if planned_care_30 > 0:
            potential_cares = planned_care_30 * 4
            care_execution_rate = round(min(100, care_in_30 / max(potential_cares, 1) * 100), 1)

        checkup_overdue = active_lenses.filter(next_checkup_date__lt=today).count()
        checkup_coming = active_lenses.filter(
            next_checkup_date__gte=today,
            next_checkup_date__lte=today + timedelta(days=30)
        ).count()

        reminder_total = CareReminder.objects.count()
        reminder_dismissed = CareReminder.objects.filter(is_dismissed=True).count()

        care_type_stats = dict(CareRecord.objects.values_list('care_type').annotate(count=Count('id')))
        reminder_type_stats = dict(CareReminder.objects.values_list('reminder_type').annotate(count=Count('id')))

        return Response({
            'total_care_records': total_care_records,
            'total_care_records_30d': care_in_30,
            'routine_care_count': routine_count,
            'checkup_count': checkup_count,
            'rest_record_count': rest_count,
            'lenses_with_care_plan': with_care_plan,
            'lenses_with_checkup_plan': lenses_with_checkup,
            'care_in_last_30_days': care_in_30,
            'care_execution_rate': care_execution_rate,
            'checkup_overdue_count': checkup_overdue,
            'checkup_coming_30_days': checkup_coming,
            'total_reminders': reminder_total,
            'dismissed_reminders': reminder_dismissed,
            'active_reminders': reminder_total - reminder_dismissed,
            'care_type_stats': care_type_stats,
            'reminder_type_stats': reminder_type_stats,
        })

    @action(detail=False, methods=['get'])
    def care_method_comfort(self, request):
        methods = ['hydrogen_peroxide', 'multi_purpose', 'daily_disposable', 'other']
        method_labels = {
            'hydrogen_peroxide': '双氧水护理',
            'multi_purpose': '多功能护理液',
            'daily_disposable': '日抛无需护理',
            'other': '其他方式',
        }
        result = []
        for method in methods:
            lenses = Lens.objects.filter(care_method=method)
            records = WearRecord.objects.filter(lens__in=lenses)
            total_records = records.count()
            if total_records == 0:
                continue
            avg_comfort = records.aggregate(Avg('comfort_level'))['comfort_level__avg'] or 0
            total_hours = records.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
            reactions_qs = records.values('eye_reaction').annotate(count=Count('id'))
            reactions = [{'eye_reaction': r['eye_reaction'], 'count': r['count']} for r in reactions_qs]
            bad_reaction_count = records.exclude(eye_reaction='none').count()
            bad_rate = round(bad_reaction_count / total_records * 100, 1)
            result.append({
                'care_method': method,
                'care_method_display': method_labels.get(method, method),
                'lens_count': lenses.count(),
                'total_records': total_records,
                'avg_comfort': round(avg_comfort, 2),
                'total_hours': round(total_hours, 1),
                'bad_reaction_rate': bad_rate,
                'reactions': reactions,
            })
        result.sort(key=lambda x: x['avg_comfort'], reverse=True)
        return Response(result)

    @action(detail=False, methods=['get'])
    def brand_comfort(self, request):
        brands = Lens.objects.values_list('brand', flat=True).distinct()
        result = []
        for brand in brands:
            brand_lenses = Lens.objects.filter(brand=brand)
            records = WearRecord.objects.filter(lens__in=brand_lenses)
            total_records = records.count()
            if total_records == 0:
                continue
            avg_comfort = records.aggregate(Avg('comfort_level'))['comfort_level__avg'] or 0
            total_hours = records.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
            result.append({
                'brand': brand,
                'avg_comfort': round(avg_comfort, 2),
                'total_records': total_records,
                'total_hours': round(total_hours, 1),
                'lens_count': brand_lenses.count()
            })
        result.sort(key=lambda x: x['avg_comfort'], reverse=True)
        return Response(result)

    @action(detail=False, methods=['get'])
    def water_content_fit(self, request):
        ranges = [
            ('<38%', 0, 38),
            ('38-42%', 38, 42),
            ('42-55%', 42, 55),
            ('55-58%', 55, 58),
            ('>58%', 58, 100),
        ]
        result = []
        for label, min_w, max_w in ranges:
            if min_w == 0:
                lenses = Lens.objects.filter(water_content__lt=max_w)
            elif max_w == 100:
                lenses = Lens.objects.filter(water_content__gte=min_w)
            else:
                lenses = Lens.objects.filter(water_content__gte=min_w, water_content__lt=max_w)
            records = WearRecord.objects.filter(lens__in=lenses)
            total_records = records.count()
            avg_comfort = records.aggregate(Avg('comfort_level'))['comfort_level__avg'] or 0
            reaction_counts = records.values('eye_reaction').annotate(count=Count('id'))
            total_hours = records.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
            result.append({
                'range': label,
                'lens_count': lenses.count(),
                'total_records': total_records,
                'avg_comfort': round(avg_comfort, 2),
                'total_hours': round(total_hours, 1),
                'reactions': list(reaction_counts)
            })
        return Response(result)

    @action(detail=False, methods=['get'])
    def purpose_stats(self, request):
        purposes = ['daily', 'date', 'photo']
        labels = {'daily': '日常', 'date': '约会', 'photo': '拍照'}
        result = []
        for p in purposes:
            lenses = Lens.objects.filter(purpose=p)
            records = WearRecord.objects.filter(lens__in=lenses)
            total_hours = records.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
            avg_comfort = records.aggregate(Avg('comfort_level'))['comfort_level__avg'] or 0
            result.append({
                'purpose': p,
                'label': labels[p],
                'lens_count': lenses.count(),
                'total_records': records.count(),
                'total_hours': round(total_hours, 1),
                'avg_comfort': round(avg_comfort, 2)
            })
        return Response(result)

    @action(detail=False, methods=['get'])
    def comfort_trend(self, request):
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        qs = WearRecord.objects.filter(wear_date__gte=start_date)
        daily_map = {}
        for r in qs:
            d = r.wear_date.isoformat()
            if d not in daily_map:
                daily_map[d] = {'date': d, 'hours': 0, 'count': 0, 'comfort_sum': 0}
            daily_map[d]['hours'] += r.duration_hours
            daily_map[d]['count'] += 1
            daily_map[d]['comfort_sum'] += r.comfort_level
        result = []
        for d, v in sorted(daily_map.items(), key=lambda x: x[0]):
            result.append({
                'date': v['date'],
                'avg_comfort': round(v['comfort_sum'] / v['count'], 2) if v['count'] else 0,
                'total_hours': round(v['hours'], 2),
                'count': v['count']
            })
        return Response(result)

    @action(detail=False, methods=['get'])
    def eye_tips(self, request):
        total_records = WearRecord.objects.count()
        tips = []
        if total_records == 0:
            tips = [
                {'level': 'info', 'title': '欢迎使用', 'content': '欢迎开始记录您的第一副彩瞳佩戴体验！'},
                {'level': 'tip', 'title': '首次佩戴建议', 'content': '建议初次佩戴者第1天不超过4小时，第2天6小时，第3天8小时，逐步适应。'},
                {'level': 'tip', 'title': '每日佩戴上限', 'content': '眼科建议单日佩戴不超过8小时，高含水量镜片不超过6小时。'},
            ]
            return Response(tips)
        total_hours = WearRecord.objects.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
        avg_hours = total_hours / total_records if total_records > 0 else 0
        bad_records = WearRecord.objects.exclude(eye_reaction='none').count()
        bad_ratio = bad_records / total_records if total_records > 0 else 0
        low_comfort = WearRecord.objects.filter(comfort_level__lte=2).count()
        recent_30 = timezone.now().date() - timedelta(days=30)
        recent_records = WearRecord.objects.filter(wear_date__gte=recent_30)
        recent_avg = recent_records.aggregate(Avg('comfort_level'))['comfort_level__avg'] or 0
        if avg_hours > 10:
            tips.append({'level': 'danger', 'title': '佩戴时长过长', 'content': f'您的平均佩戴时长为 {avg_hours:.1f} 小时/次，建议控制在8小时以内。'})
        elif avg_hours > 8:
            tips.append({'level': 'warning', 'title': '佩戴时长偏长', 'content': f'您的平均佩戴时长为 {avg_hours:.1f} 小时/次，接近建议上限，请注意休息。'})
        else:
            tips.append({'level': 'success', 'title': '佩戴习惯良好', 'content': f'您的平均佩戴时长为 {avg_hours:.1f} 小时/次，保持得很好！'})
        if bad_ratio > 0.5:
            tips.append({'level': 'danger', 'title': '眼部反应频繁', 'content': f'有 {bad_ratio*100:.0f}% 的佩戴出现不适，建议暂停佩戴并咨询眼科医生。'})
        elif bad_ratio > 0.3:
            tips.append({'level': 'warning', 'title': '眼部不适较多', 'content': f'有 {bad_ratio*100:.0f}% 的佩戴出现不适，建议尝试含水量更高或更换品牌。'})
        if low_comfort > 0:
            tips.append({'level': 'warning', 'title': '低舒适度记录', 'content': f'有 {low_comfort} 次佩戴舒适度≤2分，可考虑更换镜片品牌或参数。'})
        if recent_avg and recent_avg < 3:
            tips.append({'level': 'warning', 'title': '近期舒适度下降', 'content': f'近30天平均舒适度 {recent_avg:.1f} 分，建议检查镜片状态或更换护理液。'})
        tips.append({'level': 'tip', 'title': '护理提醒', 'content': '每周建议至少1-2天佩戴框架眼镜，让眼睛充分休息。'})
        tips.append({'level': 'tip', 'title': '开封后有效期', 'content': '日抛开封即用即抛；月抛建议开封后1个月内更换，即使未使用完。'})
        tips.append({'level': 'tip', 'title': '睡眠禁忌', 'content': '严禁佩戴普通彩瞳睡觉，午睡也不建议，会导致角膜缺氧。'})
        return Response(tips)


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
        today = timezone.now().date()
        total_plans = OutfitPlan.objects.count()
        pending_plans = OutfitPlan.objects.filter(status='pending').count()
        completed_plans = OutfitPlan.objects.filter(status='completed').count()
        cancelled_plans = OutfitPlan.objects.filter(status='cancelled').count()

        avg_match_score = OutfitPlan.objects.filter(status='completed').aggregate(
            Avg('match_score')
        )['match_score__avg'] or 0

        makeup_stats = OutfitPlan.objects.values('makeup_style', 'custom_makeup_style').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        top_makeup_styles = []
        for ms in makeup_stats:
            style_name = ms['custom_makeup_style'] if ms['custom_makeup_style'] else \
                dict(OutfitPlan.MAKEUP_STYLE_CHOICES).get(ms['makeup_style'], ms['makeup_style'])
            top_makeup_styles.append({
                'style': style_name,
                'count': ms['count']
            })

        scene_lens_stats = OutfitPlan.objects.filter(status='completed').values(
            'scene_name', 'custom_scene_name', 'lens_id', 'lens__brand', 'lens__model_name'
        ).annotate(count=Count('id')).order_by('-count')

        lens_usage_by_scene = []
        for sl in scene_lens_stats:
            scene_name = sl['custom_scene_name'] if sl['custom_scene_name'] else \
                dict(OutfitPlan.SCENE_CHOICES).get(sl['scene_name'], sl['scene_name'])
            lens_name = f"{sl['lens__brand']} {sl['lens__model_name'] or ''}" if sl['lens_id'] else '未指定'
            lens_usage_by_scene.append({
                'scene': scene_name,
                'lens': lens_name,
                'lens_id': sl['lens_id'],
                'count': sl['count']
            })

        match_score_ranking = OutfitPlan.objects.filter(status='completed').values(
            'id', 'lens_id', 'lens__brand', 'lens__model_name', 'match_score', 'scene_name', 'custom_scene_name'
        ).order_by('-match_score', '-created_at')[:10]

        ranking_list = []
        for r in match_score_ranking:
            scene_name = r['custom_scene_name'] if r['custom_scene_name'] else \
                dict(OutfitPlan.SCENE_CHOICES).get(r['scene_name'], r['scene_name'])
            ranking_list.append({
                'id': r['id'],
                'lens': f"{r['lens__brand']} {r['lens__model_name'] or ''}" if r['lens_id'] else '未指定',
                'lens_id': r['lens_id'],
                'match_score': r['match_score'],
                'scene': scene_name
            })

        upcoming_7d = OutfitPlan.objects.filter(
            status='pending',
            expected_wear_date__gte=today,
            expected_wear_date__lte=today + timedelta(days=7)
        ).order_by('expected_wear_date')[:5]

        upcoming_plans = OutfitPlanSerializer(upcoming_7d, many=True).data

        tag_stats = {}
        all_completed = OutfitPlan.objects.filter(status='completed')
        for tag_key, tag_label in OutfitPlan.TAG_CHOICES:
            count = all_completed.filter(tags__contains=tag_key).count()
            tag_stats[tag_key] = {
                'label': tag_label,
                'count': count
            }

        data = {
            'total_plans': total_plans,
            'pending_plans': pending_plans,
            'completed_plans': completed_plans,
            'cancelled_plans': cancelled_plans,
            'avg_match_score': round(avg_match_score, 1),
            'top_makeup_styles': top_makeup_styles,
            'lens_usage_by_scene': lens_usage_by_scene,
            'match_score_ranking': ranking_list,
            'upcoming_plans': upcoming_plans,
            'tag_stats': tag_stats,
        }

        serializer = OutfitPlanStatsSerializer(data)
        return Response(serializer.data)
