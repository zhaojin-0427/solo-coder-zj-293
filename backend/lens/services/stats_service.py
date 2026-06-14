from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from .exceptions import safe_service_call
from ..models import (
    Lens, WearRecord, CareRecord, CareReminder,
)


@safe_service_call(default_value={}, service_name="StatsService.Overview")
def get_stats_overview():
    """首页概览统计"""
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

    return {
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
    }


@safe_service_call(default_value={}, service_name="StatsService.Care")
def get_care_stats():
    """护理统计"""
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

    return {
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
    }


@safe_service_call(default_value=[], service_name="StatsService.CareMethodComfort")
def get_care_method_comfort():
    """护理方式舒适度对比"""
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
    return result


@safe_service_call(default_value=[], service_name="StatsService.BrandComfort")
def get_brand_comfort():
    """品牌舒适度排行"""
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
    return result


@safe_service_call(default_value=[], service_name="StatsService.WaterContentFit")
def get_water_content_fit():
    """含水量适配度分析"""
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
    return result


@safe_service_call(default_value=[], service_name="StatsService.PurposeStats")
def get_purpose_stats():
    """用途分布统计"""
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
    return result


@safe_service_call(default_value=[], service_name="StatsService.ComfortTrend")
def get_comfort_trend(days=30):
    """舒适度趋势（近N天）"""
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
    return result


@safe_service_call(default_value=[], service_name="StatsService.EyeTips")
def get_eye_tips():
    """护眼小贴士生成"""
    total_records = WearRecord.objects.count()
    tips = []
    if total_records == 0:
        tips = [
            {'level': 'info', 'title': '欢迎使用', 'content': '欢迎开始记录您的第一副彩瞳佩戴体验！'},
            {'level': 'tip', 'title': '首次佩戴建议', 'content': '建议初次佩戴者第1天不超过4小时，第2天6小时，第3天8小时，逐步适应。'},
            {'level': 'tip', 'title': '每日佩戴上限', 'content': '眼科建议单日佩戴不超过8小时，高含水量镜片不超过6小时。'},
        ]
        return tips
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
    return tips
