from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta

from .exceptions import safe_service_call
from ..models import (
    Lens, PurchaseRecord, RestockSuggestion,
)
from ..serializers import (
    LensSerializer, RestockSuggestionSerializer,
)


@safe_service_call(default_value=[], service_name="BudgetService.RestockSuggestions")
def generate_restock_suggestions():
    """生成补货建议"""
    today = timezone.now().date()
    suggestions = []

    active_lenses = Lens.objects.exclude(status__in=['used_up', 'expired'])

    for lens in active_lenses:
        remaining = lens.get_remaining_stock()
        estimated_days = lens.get_estimated_days_left()
        days_until_expiry = lens.days_until_expiry()
        days_since_wear = lens.get_days_since_last_wear()
        avg_comfort = lens.get_avg_comfort_level()

        if remaining <= 0:
            exists = RestockSuggestion.objects.filter(
                lens=lens,
                suggestion_type='low_stock',
                is_action_taken=False,
                is_dismissed=False
            ).exists()
            if not exists:
                suggestions.append(RestockSuggestion(
                    lens=lens,
                    suggestion_type='low_stock',
                    severity='critical',
                    title=f'{lens.brand} {lens.model_name} 库存已用完',
                    message=f'该镜片库存已耗尽，请及时补货。建议补货数量：{lens.replacement_days_after_open or 30}天用量。',
                    current_stock=remaining,
                    estimated_days_left=0,
                    suggested_quantity=max(2, lens.stock_quantity),
                    suggested_date=today
                ))

        elif estimated_days is not None and estimated_days <= 7:
            exists = RestockSuggestion.objects.filter(
                lens=lens,
                suggestion_type='low_stock',
                is_action_taken=False,
                is_dismissed=False
            ).exists()
            if not exists:
                suggestions.append(RestockSuggestion(
                    lens=lens,
                    suggestion_type='low_stock',
                    severity='critical',
                    title=f'{lens.brand} {lens.model_name} 库存紧急',
                    message=f'按当前使用频率，预计仅能使用 {estimated_days} 天。建议立即补货。',
                    current_stock=remaining,
                    estimated_days_left=estimated_days,
                    suggested_quantity=max(2, int(lens.get_monthly_usage_rate())),
                    suggested_date=today
                ))

        elif remaining <= 2:
            exists = RestockSuggestion.objects.filter(
                lens=lens,
                suggestion_type='low_stock',
                is_action_taken=False,
                is_dismissed=False
            ).exists()
            if not exists:
                suggestions.append(RestockSuggestion(
                    lens=lens,
                    suggestion_type='low_stock',
                    severity='important',
                    title=f'{lens.brand} {lens.model_name} 库存不足',
                    message=f'当前库存仅剩 {remaining} 片，建议尽快补货。',
                    current_stock=remaining,
                    estimated_days_left=estimated_days,
                    suggested_quantity=2,
                    suggested_date=today + timedelta(days=3)
                ))

        if days_until_expiry <= 30 and remaining > 0:
            exists = RestockSuggestion.objects.filter(
                lens=lens,
                suggestion_type='expiring_soon',
                is_action_taken=False,
                is_dismissed=False
            ).exists()
            if not exists:
                suggestions.append(RestockSuggestion(
                    lens=lens,
                    suggestion_type='expiring_soon',
                    severity='important',
                    title=f'{lens.brand} {lens.model_name} 即将过期但仍有库存',
                    message=f'该镜片将于 {days_until_expiry} 天后过期，但仍有 {remaining} 片库存。建议优先使用，避免重复购买。',
                    current_stock=remaining,
                    estimated_days_left=days_until_expiry,
                    suggested_quantity=0,
                    suggested_date=today
                ))

        if days_since_wear >= 90 and remaining > 0:
            exists = RestockSuggestion.objects.filter(
                lens=lens,
                suggestion_type='long_unused',
                is_action_taken=False,
                is_dismissed=False
            ).exists()
            if not exists:
                suggestions.append(RestockSuggestion(
                    lens=lens,
                    suggestion_type='long_unused',
                    severity='normal',
                    title=f'{lens.brand} {lens.model_name} 长期未使用',
                    message=f'该镜片已 {days_since_wear} 天未佩戴，但仍有 {remaining} 片库存。请检查是否需要继续补货。',
                    current_stock=remaining,
                    estimated_days_left=None,
                    suggested_quantity=0,
                    suggested_date=today
                ))

        if avg_comfort is not None and avg_comfort <= 2 and lens.get_total_spent() > 0:
            exists = RestockSuggestion.objects.filter(
                lens=lens,
                suggestion_type='low_comfort',
                is_action_taken=False,
                is_dismissed=False
            ).exists()
            if not exists:
                cost_per_wear = lens.get_cost_per_wear()
                suggestions.append(RestockSuggestion(
                    lens=lens,
                    suggestion_type='low_comfort',
                    severity='important',
                    title=f'{lens.brand} {lens.model_name} 低舒适度高花费预警',
                    message=f'该镜片平均舒适度仅 {avg_comfort} 分，但已花费 ¥{lens.get_total_spent():.2f}。'
                            f'每次佩戴成本约 ¥{cost_per_wear:.2f}。建议考虑更换品牌。',
                    current_stock=remaining,
                    estimated_days_left=estimated_days,
                    suggested_quantity=0,
                    suggested_date=today
                ))

        if lens.planned_restock_date and (lens.planned_restock_date - today).days <= 7 and (lens.planned_restock_date - today).days >= 0:
            exists = RestockSuggestion.objects.filter(
                lens=lens,
                suggestion_type='planned',
                is_action_taken=False,
                is_dismissed=False
            ).exists()
            if not exists:
                suggestions.append(RestockSuggestion(
                    lens=lens,
                    suggestion_type='planned',
                    severity='normal',
                    title=f'{lens.brand} {lens.model_name} 计划补货日期临近',
                    message=f'计划补货日期为 {lens.planned_restock_date}，请按时补货。',
                    current_stock=remaining,
                    estimated_days_left=estimated_days,
                    suggested_quantity=2,
                    suggested_date=lens.planned_restock_date
                ))

        monthly_rate = lens.get_monthly_usage_rate()
        if monthly_rate >= 10 and estimated_days is not None and estimated_days <= 14:
            exists = RestockSuggestion.objects.filter(
                lens=lens,
                suggestion_type='high_usage',
                is_action_taken=False,
                is_dismissed=False
            ).exists()
            if not exists:
                suggestions.append(RestockSuggestion(
                    lens=lens,
                    suggestion_type='high_usage',
                    severity='important',
                    title=f'{lens.brand} {lens.model_name} 使用频率高',
                    message=f'近3个月平均每月使用 {monthly_rate} 次，属于高频使用。建议批量采购，降低单次购买成本。',
                    current_stock=remaining,
                    estimated_days_left=estimated_days,
                    suggested_quantity=4,
                    suggested_date=today + timedelta(days=7)
                ))

    if suggestions:
        RestockSuggestion.objects.bulk_create(suggestions)

    return suggestions


@safe_service_call(default_value={}, service_name="BudgetService.Stats")
def get_budget_stats(budget_month=None, budget_limit=500):
    """预算统计"""
    today = timezone.now().date()
    if budget_month is None:
        budget_month = today.strftime('%Y-%m')
    budget_limit = float(budget_limit)

    year = budget_month[:4]
    month_start = f'{budget_month}-01'
    next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
    month_end = (next_month - timedelta(days=1)).isoformat()

    month_records = PurchaseRecord.objects.filter(
        purchase_date__gte=month_start,
        purchase_date__lte=month_end
    )
    year_records = PurchaseRecord.objects.filter(purchase_date__startswith=year)

    total_spent_month = float(month_records.aggregate(Sum('actual_paid'))['actual_paid__sum'] or 0)
    total_spent_year = float(year_records.aggregate(Sum('actual_paid'))['actual_paid__sum'] or 0)
    total_purchases_month = month_records.count()
    total_purchases_year = year_records.count()

    budget_used_percent = round((total_spent_month / budget_limit * 100) if budget_limit > 0 else 0, 2)
    is_over_budget = total_spent_month > budget_limit

    brand_spending_qs = month_records.values(
        'lens__brand'
    ).annotate(
        total=Sum('actual_paid'),
        count=Count('id')
    ).order_by('-total')

    brand_spending = []
    for bs in brand_spending_qs:
        brand_spending.append({
            'brand': bs['lens__brand'] or '未知品牌',
            'total': float(bs['total']),
            'count': bs['count'],
            'percent': round(float(bs['total']) / total_spent_month * 100, 1) if total_spent_month > 0 else 0
        })

    channel_spending_qs = month_records.values(
        'purchase_channel', 'custom_channel'
    ).annotate(
        total=Sum('actual_paid'),
        count=Count('id')
    ).order_by('-total')

    channel_spending = []
    channel_labels = dict(PurchaseRecord.CHANNEL_CHOICES)
    for cs in channel_spending_qs:
        channel_name = cs['custom_channel'] or channel_labels.get(cs['purchase_channel'], cs['purchase_channel'])
        channel_spending.append({
            'channel': channel_name,
            'channel_key': cs['purchase_channel'],
            'total': float(cs['total']),
            'count': cs['count'],
            'percent': round(float(cs['total']) / total_spent_month * 100, 1) if total_spent_month > 0 else 0
        })

    all_purchases = PurchaseRecord.objects.all()
    channel_price_map = {}
    for pr in all_purchases:
        channel = pr.get_channel_display_name()
        if channel not in channel_price_map:
            channel_price_map[channel] = {'prices': [], 'count': 0}
        if float(pr.unit_price) > 0:
            channel_price_map[channel]['prices'].append(float(pr.unit_price))
        channel_price_map[channel]['count'] += 1

    channel_price_comparison = []
    for channel, data in channel_price_map.items():
        if data['prices']:
            avg_price = sum(data['prices']) / len(data['prices'])
            min_price = min(data['prices'])
            max_price = max(data['prices'])
            channel_price_comparison.append({
                'channel': channel,
                'avg_price': round(avg_price, 2),
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2),
                'purchase_count': data['count']
            })
    channel_price_comparison.sort(key=lambda x: x['avg_price'])

    monthly_trend = []
    for m in range(11, -1, -1):
        month_date = today - timedelta(days=m * 30)
        m_str = month_date.strftime('%Y-%m')
        m_records = PurchaseRecord.objects.filter(budget_month=m_str)
        m_total = float(m_records.aggregate(Sum('actual_paid'))['actual_paid__sum'] or 0)
        m_count = m_records.count()
        monthly_trend.append({
            'month': m_str,
            'total_spent': round(m_total, 2),
            'purchase_count': m_count
        })

    brand_value_qs = Lens.objects.exclude(status='expired').annotate(
        total_spent=Sum('purchase_records__actual_paid'),
        total_wears=Count('wear_records'),
        avg_comfort=Avg('wear_records__comfort_level')
    ).filter(total_spent__gt=0, total_wears__gt=0)

    brand_value_ranking = []
    for lens in brand_value_qs:
        cost_per_wear = float(lens.total_spent) / lens.total_wears if lens.total_wears > 0 else 0
        value_score = (float(lens.avg_comfort or 0) * 100) / (cost_per_wear + 1)
        brand_value_ranking.append({
            'lens_id': lens.id,
            'brand': lens.brand,
            'model': lens.model_name,
            'total_spent': float(lens.total_spent),
            'total_wears': lens.total_wears,
            'avg_comfort': round(float(lens.avg_comfort or 0), 1),
            'cost_per_wear': round(cost_per_wear, 2),
            'value_score': round(value_score, 2)
        })
    brand_value_ranking.sort(key=lambda x: x['value_score'], reverse=True)

    low_comfort_high_cost = []
    active_lenses = Lens.objects.exclude(status__in=['used_up', 'expired'])
    for lens in active_lenses:
        if lens.is_low_comfort_high_cost():
            low_comfort_high_cost.append({
                'lens_id': lens.id,
                'brand': lens.brand,
                'model': lens.model_name,
                'avg_comfort': lens.get_avg_comfort_level(),
                'total_spent': lens.get_total_spent(),
                'cost_per_wear': lens.get_cost_per_wear(),
                'remaining_stock': lens.get_remaining_stock()
            })

    expiring_with_stock = []
    running_out_soon = []
    for lens in active_lenses:
        restock_status = lens.get_restock_status()
        if restock_status['status'] == 'expiring_with_stock':
            expiring_with_stock.append(LensSerializer(lens).data)
        elif restock_status['status'] in ['urgent', 'low', 'out_of_stock']:
            running_out_soon.append(LensSerializer(lens).data)

    restock_suggestions = RestockSuggestion.objects.filter(
        is_dismissed=False,
        is_action_taken=False
    ).order_by('-severity', '-triggered_at')[:10]
    restock_suggestions_data = RestockSuggestionSerializer(restock_suggestions, many=True).data

    return {
        'total_spent_month': round(total_spent_month, 2),
        'total_spent_year': round(total_spent_year, 2),
        'total_purchases_month': total_purchases_month,
        'total_purchases_year': total_purchases_year,
        'budget_month': budget_month,
        'budget_limit': budget_limit,
        'budget_used_percent': budget_used_percent,
        'is_over_budget': is_over_budget,
        'brand_spending': brand_spending,
        'channel_spending': channel_spending,
        'channel_price_comparison': channel_price_comparison,
        'monthly_trend': monthly_trend,
        'brand_value_ranking': brand_value_ranking[:10],
        'low_comfort_high_cost': low_comfort_high_cost,
        'expiring_with_stock': expiring_with_stock,
        'running_out_soon': running_out_soon,
        'restock_suggestions': restock_suggestions_data
    }


@safe_service_call(default_value=[], service_name="BudgetService.MonthlySummary")
def get_budget_monthly_summary():
    """月度消费摘要（近12个月）"""
    today = timezone.now().date()
    months = []
    for m in range(11, -1, -1):
        month_date = today - timedelta(days=m * 30)
        m_str = month_date.strftime('%Y-%m')
        m_records = PurchaseRecord.objects.filter(budget_month=m_str)
        m_total = float(m_records.aggregate(Sum('actual_paid'))['actual_paid__sum'] or 0)
        m_count = m_records.count()
        m_brands = m_records.values('lens__brand').distinct().count()
        months.append({
            'month': m_str,
            'month_label': month_date.strftime('%Y年%m月'),
            'total_spent': round(m_total, 2),
            'purchase_count': m_count,
            'brand_count': m_brands
        })
    return months
