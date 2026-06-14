from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from .exceptions import safe_service_call
from ..models import (
    TravelPlan, TravelLensItem, TravelSupplyItem, TravelDailyPlan, TravelRiskAlert,
    Lens, WearRecord,
)


@safe_service_call(default_value=None, service_name="TravelService.CalculateRisk")
def calculate_travel_risk_level(plan):
    """计算旅行风险等级"""
    risk_score = 0
    high_risk_climates = ['dry_hot', 'highland', 'cold_dry']
    if plan.climate in high_risk_climates:
        risk_score += 2

    lens_items = plan.lens_items.all()
    total_pairs = sum(item.quantity for item in lens_items)
    duration = plan.get_duration_days()
    if total_pairs < duration:
        risk_score += 2
    elif total_pairs < duration + 2:
        risk_score += 1

    has_care_solution = plan.supplies.filter(supply_type='care_solution', is_checked=True).exists()
    has_lens_case = plan.supplies.filter(supply_type='lens_case', is_checked=True).exists()
    has_eye_drops = plan.supplies.filter(supply_type='eye_drops', is_checked=True).exists()

    care_needed_lenses = lens_items.filter(lens__care_method__in=['hydrogen_peroxide', 'multi_purpose', 'other'])
    if care_needed_lenses.exists() and not has_care_solution:
        risk_score += 2
    if care_needed_lenses.exists() and not has_lens_case:
        risk_score += 1

    if plan.climate in ['dry_hot', 'highland'] and not has_eye_drops:
        risk_score += 1

    for item in lens_items:
        if item.lens and item.lens.expiry_date <= plan.end_date:
            risk_score += 2

    if risk_score >= 4:
        plan.risk_level = 'high'
    elif risk_score >= 2:
        plan.risk_level = 'medium'
    else:
        plan.risk_level = 'low'
    plan.save()
    return plan.risk_level


@safe_service_call(default_value=([], []), service_name="TravelService.GenerateSuggestions")
def generate_travel_suggestions_and_risks(plan):
    """生成旅行建议和风险提醒"""
    suggestions = []
    risks = []
    today = timezone.now().date()
    duration = plan.get_duration_days()

    if plan.climate in ['dry_hot', 'highland']:
        suggestions.append({
            'type': 'climate',
            'level': 'warning',
            'title': '高温干燥地区建议减少佩戴',
            'message': f'目的地「{plan.destination}」气候较为干燥炎热，建议减少每日佩戴时长，多使用润眼液，准备框架眼镜作为替代。'
        })
        risks.append({
            'type': 'climate_dry',
            'level': 'warning',
            'title': '干燥气候可能加重眼部干涩',
            'message': '干燥环境下泪液蒸发加快，建议随身携带润眼液，每日佩戴不超过6小时。'
        })

    if plan.climate == 'cold_dry':
        suggestions.append({
            'type': 'climate',
            'level': 'info',
            'title': '寒冷干燥地区佩戴建议',
            'message': '室内外温差大，注意镜片适应，建议准备框架眼镜在室内交替佩戴。'
        })

    if plan.climate in ['tropical_humid', 'subtropical_humid', 'marine']:
        suggestions.append({
            'type': 'climate',
            'level': 'info',
            'title': '潮湿地区护理提醒',
            'message': '潮湿气候下细菌容易滋生，请严格按照护理流程清洁镜片，护理液开封后按时更换。'
        })

    lens_items = plan.lens_items.all()
    primary_items = lens_items.filter(role='primary')
    backup_items = lens_items.filter(role='backup')

    total_pairs = sum(item.quantity for item in lens_items)
    if total_pairs == 0:
        risks.append({
            'type': 'no_lens',
            'level': 'danger',
            'title': '尚未添加携带镜片',
            'message': '请从镜片库选择主带镜片和备用镜片添加到旅行方案中。'
        })
    elif total_pairs < duration:
        risks.append({
            'type': 'insufficient_lens',
            'level': 'danger',
            'title': '备用镜片不足',
            'message': f'旅行共{duration}天，但仅携带{total_pairs}片镜片，建议至少携带{duration + 2}片以备不时之需。'
        })
    elif backup_items.count() == 0:
        suggestions.append({
            'type': 'backup',
            'level': 'warning',
            'title': '建议添加备用镜片',
            'message': '旅行期间可能出现镜片丢失、破损等情况，建议至少准备1-2副备用镜片。'
        })

    for item in lens_items:
        if not item.lens:
            continue
        lens = item.lens
        if lens.expiry_date <= plan.end_date:
            days_left = (lens.expiry_date - plan.start_date).days
            risks.append({
                'type': 'expiry',
                'level': 'danger',
                'title': '旅行期间将过期',
                'message': f'镜片「{lens.brand} {lens.model_name}」将于{lens.expiry_date}过期，旅行第{max(1, days_left + 1)}天后失效，建议更换新镜片。',
                'lens_id': lens.id
            })

        if lens.open_date and lens.replacement_days_after_open:
            days_open_at_start = (plan.start_date - lens.open_date).days
            if days_open_at_start >= lens.replacement_days_after_open:
                risks.append({
                    'type': 'overdue_replacement',
                    'level': 'danger',
                    'title': '镜片已超过建议更换周期',
                    'message': f'镜片「{lens.brand} {lens.model_name}」已开封{days_open_at_start}天，超过建议更换周期({lens.replacement_days_after_open}天)，建议更换新镜片。',
                    'lens_id': lens.id
                })
            elif days_open_at_start + duration > lens.replacement_days_after_open:
                suggestions.append({
                    'type': 'replacement_during_trip',
                    'level': 'warning',
                    'title': '旅行期间需更换镜片',
                    'message': f'镜片「{lens.brand} {lens.model_name}」在旅行第{lens.replacement_days_after_open - days_open_at_start + 1}天需更换，请备好替换镜片。',
                    'lens_id': lens.id
                })

        if lens.is_under_rest():
            risks.append({
                'type': 'under_rest',
                'level': 'warning',
                'title': '镜片处于停戴观察期',
                'message': f'镜片「{lens.brand} {lens.model_name}」目前处于停戴观察期{"，至" + str(lens.rest_until_date) if lens.rest_until_date else ""}，建议不要携带或更换镜片。',
                'lens_id': lens.id
            })

        remaining = lens.get_remaining_stock()
        if remaining < item.quantity:
            risks.append({
                'type': 'insufficient_stock',
                'level': 'warning',
                'title': '库存不足',
                'message': f'镜片「{lens.brand} {lens.model_name}」剩余库存{remaining}片，少于计划携带的{item.quantity}片。',
                'lens_id': lens.id
            })

    care_needed = any(item.lens and item.lens.care_method in ['hydrogen_peroxide', 'multi_purpose', 'other'] for item in lens_items)
    has_care_solution = plan.supplies.filter(supply_type='care_solution', is_checked=True).exists()
    has_lens_case = plan.supplies.filter(supply_type='lens_case', is_checked=True).exists()
    has_eye_drops = plan.supplies.filter(supply_type='eye_drops', is_checked=True).exists()

    if care_needed and not has_care_solution:
        risks.append({
            'type': 'missing_supply',
            'level': 'danger',
            'title': '护理用品未勾选',
            'message': '携带的非日抛镜片需要护理液，请在随身用品中勾选并准备护理液。'
        })

    if care_needed and not has_lens_case:
        risks.append({
            'type': 'missing_supply',
            'level': 'warning',
            'title': '镜盒未勾选',
            'message': '非日抛镜片需要镜盒存放，请在随身用品中勾选镜盒。'
        })

    if plan.climate in ['dry_hot', 'highland', 'cold_dry'] and not has_eye_drops:
        suggestions.append({
            'type': 'missing_supply',
            'level': 'warning',
            'title': '建议携带润眼液',
            'message': f'目的地气候较为{"干燥" if plan.climate != "highland" else "高原"}，建议携带润眼液缓解眼部不适。'
        })

    if plan.luggage == 'carry_on':
        suggestions.append({
            'type': 'luggage',
            'level': 'info',
            'title': '随身行李携带提醒',
            'message': '随身行李液体通常限制为100ml以下，请将护理液分装或托运，确认航空公司规定。'
        })

    if plan.transport in ['airplane', 'ship']:
        suggestions.append({
            'type': 'transport',
            'level': 'info',
            'title': '长途交通佩戴建议',
            'message': '长途行程中客舱空气干燥，建议减少佩戴时长或佩戴框架眼镜，多眨眼保持眼部湿润。'
        })

    avg_comfort_map = {}
    for item in lens_items:
        if item.lens:
            avg = item.lens.get_avg_comfort_level()
            if avg is not None:
                avg_comfort_map[item.lens.id] = avg
    low_comfort_lenses = [lid for lid, avg in avg_comfort_map.items() if avg <= 2]
    if low_comfort_lenses:
        for item in lens_items:
            if item.lens and item.lens.id in low_comfort_lenses:
                suggestions.append({
                    'type': 'comfort',
                    'level': 'warning',
                    'title': '历史舒适度偏低提醒',
                    'message': f'镜片「{item.lens.brand} {item.lens.model_name}」历史平均舒适度仅{avg_comfort_map[item.lens.id]}分，旅行中长时间佩戴可能引起不适，建议备换。',
                    'lens_id': item.lens.id
                })

    daily_plans = plan.daily_plans.all()
    if daily_plans.exists():
        total_planned_hours = sum(p.expected_duration_hours or 0 for p in daily_plans)
        avg_daily_hours = total_planned_hours / len(daily_plans) if daily_plans else 0
        if avg_daily_hours > 10:
            risks.append({
                'type': 'long_hours',
                'level': 'warning',
                'title': '日均佩戴时长过长',
                'message': f'计划日均佩戴{avg_daily_hours:.1f}小时，超过建议上限(8小时)，建议减少每日佩戴时长，准备框架眼镜交替。'
            })

    return suggestions, risks


@safe_service_call(default_value=None, service_name="TravelService.UpdateStatus")
def update_travel_auto_status(plan):
    """更新旅行计划自动状态"""
    today = timezone.now().date()
    if plan.status in ['completed', 'cancelled']:
        return plan.status
    if today > plan.end_date:
        plan.status = 'completed'
    elif today >= plan.start_date:
        plan.status = 'in_progress'
    elif (plan.start_date - today).days <= 7:
        plan.status = 'upcoming'
    else:
        plan.status = 'planning'
    plan.save()
    return plan.status


@safe_service_call(default_value={}, service_name="TravelService.Stats")
def get_travel_plan_stats():
    """旅行统计数据"""
    from ..models import OutfitPlan

    all_plans = TravelPlan.objects.all()
    for plan in all_plans:
        update_travel_auto_status(plan)

    total_plans = all_plans.count()
    total_travel_days = sum(p.get_duration_days() for p in all_plans)

    status_counts = dict(all_plans.values_list('status').annotate(count=Count('id')))
    risk_counts = dict(all_plans.values_list('risk_level').annotate(count=Count('id')))

    total_alerts = TravelRiskAlert.objects.count()
    alert_type_stats = dict(TravelRiskAlert.objects.values_list('alert_type').annotate(count=Count('id')))

    climate_stats = dict(all_plans.values_list('climate').annotate(count=Count('id')))

    destination_stats_qs = all_plans.values('destination').annotate(count=Count('id')).order_by('-count')[:10]
    destination_stats = list(destination_stats_qs)

    lens_usage_qs = TravelLensItem.objects.values(
        'lens_id', 'lens__brand', 'lens__model_name'
    ).annotate(
        count=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('-count', '-total_quantity')

    lens_usage_ranking = []
    for item in lens_usage_qs:
        if not item['lens_id']:
            continue
        lens = Lens.objects.filter(id=item['lens_id']).first()
        avg_comfort = None
        avg_duration = 0
        if lens:
            avg_comfort = lens.get_avg_comfort_level()
            wear_records = WearRecord.objects.filter(lens=lens)
            total_dur = wear_records.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
            cnt = wear_records.count()
            avg_duration = round(total_dur / cnt, 1) if cnt > 0 else 0

        lens_usage_ranking.append({
            'lens_id': item['lens_id'],
            'brand': item['lens__brand'] or '-',
            'model': item['lens__model_name'] or '-',
            'travel_count': item['count'],
            'count': item['count'],
            'total_quantity': item['total_quantity'],
            'avg_comfort': avg_comfort,
            'avg_duration_hours': avg_duration
        })

    comfort_ranking = sorted(
        [x for x in lens_usage_ranking if x['avg_comfort'] is not None],
        key=lambda x: x['avg_comfort'],
        reverse=True
    )[:10]

    common_supplies_qs = TravelSupplyItem.objects.values(
        'supply_type', 'custom_name'
    ).annotate(count=Count('id')).order_by('-count')
    common_supplies = list(common_supplies_qs)

    return {
        'total_plans': total_plans,
        'total_travel_days': total_travel_days,
        'status_counts': status_counts,
        'risk_counts': risk_counts,
        'total_alerts': total_alerts,
        'alert_type_stats': alert_type_stats,
        'climate_stats': climate_stats,
        'destination_stats': destination_stats,
        'lens_usage_ranking': lens_usage_ranking,
        'comfort_ranking': comfort_ranking,
        'common_supplies': common_supplies,
    }
