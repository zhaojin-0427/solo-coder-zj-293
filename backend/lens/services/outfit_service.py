from django.db.models import Avg, Count
from django.utils import timezone

from .exceptions import safe_service_call
from ..models import OutfitPlan
from ..serializers import OutfitPlanSerializer


@safe_service_call(default_value={}, service_name="OutfitService.Stats")
def get_outfit_plan_stats():
    """妆容搭配计划统计"""
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

    today = timezone.now().date()
    upcoming_7d = OutfitPlan.objects.filter(
        status='pending',
        expected_wear_date__gte=today,
        expected_wear_date__lte=today + timezone.timedelta(days=7)
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

    return {
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
