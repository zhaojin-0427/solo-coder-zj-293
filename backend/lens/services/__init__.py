from .exceptions import safe_service_call, ServiceError
from .reminder_service import generate_reminders_from_record
from .stats_service import (
    get_stats_overview,
    get_care_stats,
    get_care_method_comfort,
    get_brand_comfort,
    get_water_content_fit,
    get_purpose_stats,
    get_comfort_trend,
    get_eye_tips,
)
from .budget_service import (
    generate_restock_suggestions,
    get_budget_stats,
    get_budget_monthly_summary,
)
from .travel_service import (
    calculate_travel_risk_level,
    generate_travel_suggestions_and_risks,
    get_travel_plan_stats,
    update_travel_auto_status,
)
from .outfit_service import get_outfit_plan_stats

__all__ = [
    'safe_service_call',
    'ServiceError',
    'generate_reminders_from_record',
    'get_stats_overview',
    'get_care_stats',
    'get_care_method_comfort',
    'get_brand_comfort',
    'get_water_content_fit',
    'get_purpose_stats',
    'get_comfort_trend',
    'get_eye_tips',
    'generate_restock_suggestions',
    'get_budget_stats',
    'get_budget_monthly_summary',
    'calculate_travel_risk_level',
    'generate_travel_suggestions_and_risks',
    'get_travel_plan_stats',
    'update_travel_auto_status',
    'get_outfit_plan_stats',
]
