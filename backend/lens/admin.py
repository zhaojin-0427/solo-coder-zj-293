from django.contrib import admin
from .models import (
    Lens, WearRecord, CareRecord, CareReminder, OutfitPlan,
    PurchaseRecord, RestockSuggestion,
    TravelPlan, TravelLensItem, TravelSupplyItem, TravelDailyPlan, TravelRiskAlert
)


@admin.register(Lens)
class LensAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model_name', 'power_sph', 'water_content', 'purpose', 'status', 'purchase_date', 'expiry_date')
    list_filter = ('status', 'purpose', 'brand')
    search_fields = ('brand', 'model_name', 'color')
    date_hierarchy = 'expiry_date'


@admin.register(WearRecord)
class WearRecordAdmin(admin.ModelAdmin):
    list_display = ('lens', 'wear_date', 'duration_hours', 'comfort_level', 'eye_reaction')
    list_filter = ('wear_date', 'comfort_level', 'eye_reaction')
    search_fields = ('lens__brand', 'notes')
    date_hierarchy = 'wear_date'


@admin.register(TravelPlan)
class TravelPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'destination', 'start_date', 'end_date', 'status', 'risk_level', 'climate', 'transport')
    list_filter = ('status', 'risk_level', 'climate', 'transport')
    search_fields = ('name', 'destination', 'notes')
    date_hierarchy = 'start_date'


@admin.register(TravelLensItem)
class TravelLensItemAdmin(admin.ModelAdmin):
    list_display = ('travel_plan', 'lens', 'role', 'quantity')
    list_filter = ('role',)
    search_fields = ('travel_plan__name', 'lens__brand')


@admin.register(TravelSupplyItem)
class TravelSupplyItemAdmin(admin.ModelAdmin):
    list_display = ('travel_plan', 'supply_type', 'custom_name', 'is_checked', 'quantity')
    list_filter = ('supply_type', 'is_checked')
    search_fields = ('travel_plan__name', 'custom_name')


@admin.register(TravelDailyPlan)
class TravelDailyPlanAdmin(admin.ModelAdmin):
    list_display = ('travel_plan', 'plan_date', 'day_label', 'planned_activity', 'expected_duration_hours')
    list_filter = ('plan_date',)
    search_fields = ('travel_plan__name', 'planned_activity', 'notes')


@admin.register(TravelRiskAlert)
class TravelRiskAlertAdmin(admin.ModelAdmin):
    list_display = ('travel_plan', 'alert_type', 'severity', 'title', 'is_dismissed', 'created_at')
    list_filter = ('alert_type', 'severity', 'is_dismissed')
    search_fields = ('travel_plan__name', 'title', 'message')
    date_hierarchy = 'created_at'
