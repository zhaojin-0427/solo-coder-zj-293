from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Lens, WearRecord
from .serializers import LensSerializer, WearRecordSerializer


class LensViewSet(viewsets.ModelViewSet):
    queryset = Lens.objects.all()
    serializer_class = LensSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        purpose_filter = self.request.query_params.get('purpose')
        brand_filter = self.request.query_params.get('brand')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if purpose_filter:
            qs = qs.filter(purpose=purpose_filter)
        if brand_filter:
            qs = qs.filter(brand__icontains=brand_filter)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        today = timezone.now().date()
        for obj in self.queryset:
            records = WearRecord.objects.filter(lens=obj)
            total_hours = records.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
            last_wear = records.order_by('-wear_date').first()
            avg_comfort = records.aggregate(Avg('comfort_level'))['comfort_level__avg']
            obj.total_wear_hours = round(total_hours, 1)
            obj.last_wear_date = last_wear.wear_date if last_wear else None
            obj.avg_comfort = round(avg_comfort, 1) if avg_comfort else None
        return context

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
        return Response({
            'total_lenses': total_lenses,
            'active_lenses': active_lenses,
            'total_records': total_records,
            'total_hours': round(total_hours, 1),
            'avg_comfort': round(avg_comfort, 1),
            'expiring_count': expiring_count,
            'expired_count': expired_count,
        })

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
