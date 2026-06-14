from rest_framework import serializers
from django.db.models import Sum, Avg, Count
from .models import (
    Lens, WearRecord, CareRecord, CareReminder, OutfitPlan, PurchaseRecord, RestockSuggestion,
    TravelPlan, TravelLensItem, TravelSupplyItem, TravelDailyPlan, TravelRiskAlert
)


class LensSerializer(serializers.ModelSerializer):
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    daily_wear_limit = serializers.SerializerMethodField()
    total_wear_hours = serializers.SerializerMethodField()
    last_wear_date = serializers.SerializerMethodField()
    avg_comfort = serializers.SerializerMethodField()
    days_since_open = serializers.SerializerMethodField()
    days_until_next_care = serializers.SerializerMethodField()
    days_until_next_checkup = serializers.SerializerMethodField()
    days_until_replacement = serializers.SerializerMethodField()
    is_under_rest = serializers.SerializerMethodField()
    care_status = serializers.SerializerMethodField()
    care_method_display = serializers.CharField(source='get_care_method_display', read_only=True)
    replacement_days_display = serializers.CharField(
        source='get_replacement_days_after_open_display', read_only=True
    )
    active_reminders = serializers.SerializerMethodField()
    last_care_date = serializers.SerializerMethodField()
    last_checkup_date = serializers.SerializerMethodField()

    remaining_stock = serializers.SerializerMethodField()
    monthly_usage_rate = serializers.SerializerMethodField()
    estimated_days_left = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    days_since_last_wear = serializers.SerializerMethodField()
    restock_status = serializers.SerializerMethodField()
    cost_per_wear = serializers.SerializerMethodField()
    is_low_comfort_high_cost = serializers.SerializerMethodField()
    usage_frequency_display = serializers.CharField(source='get_usage_frequency_display', read_only=True)
    restock_priority_display = serializers.CharField(source='get_restock_priority_display', read_only=True)
    purchase_records_count = serializers.SerializerMethodField()
    active_restock_suggestions = serializers.SerializerMethodField()
    in_upcoming_travel = serializers.SerializerMethodField()
    upcoming_travel_plans = serializers.SerializerMethodField()

    class Meta:
        model = Lens
        fields = '__all__'

    def get_is_expired(self, obj):
        return obj.is_expired()

    def get_days_until_expiry(self, obj):
        return obj.days_until_expiry()

    def get_daily_wear_limit(self, obj):
        return obj.daily_wear_limit()

    def get_total_wear_hours(self, obj):
        total = obj.wear_records.aggregate(Sum('duration_hours'))['duration_hours__sum'] or 0
        return round(total, 1)

    def get_last_wear_date(self, obj):
        last = obj.wear_records.order_by('-wear_date').first()
        return last.wear_date.isoformat() if last else None

    def get_avg_comfort(self, obj):
        avg = obj.wear_records.aggregate(Avg('comfort_level'))['comfort_level__avg']
        return round(avg, 1) if avg else None

    def get_days_since_open(self, obj):
        return obj.days_since_open()

    def get_days_until_next_care(self, obj):
        return obj.days_until_next_care()

    def get_days_until_next_checkup(self, obj):
        return obj.days_until_next_checkup()

    def get_days_until_replacement(self, obj):
        return obj.days_until_replacement()

    def get_is_under_rest(self, obj):
        return obj.is_under_rest()

    def get_care_status(self, obj):
        return obj.get_care_status()

    def get_active_reminders(self, obj):
        reminders = obj.reminders.filter(is_dismissed=False, is_read=False)[:3]
        return CareReminderSerializer(reminders, many=True).data

    def get_last_care_date(self, obj):
        last = obj.care_records.filter(
            care_type__in=['routine', 'deep_clean', 'case_replace', 'solution_replace']
        ).order_by('-care_date').first()
        return last.care_date.isoformat() if last else None

    def get_last_checkup_date(self, obj):
        last = obj.care_records.filter(care_type='checkup').order_by('-care_date').first()
        return last.care_date.isoformat() if last else None

    def get_remaining_stock(self, obj):
        return obj.get_remaining_stock()

    def get_monthly_usage_rate(self, obj):
        return obj.get_monthly_usage_rate()

    def get_estimated_days_left(self, obj):
        return obj.get_estimated_days_left()

    def get_total_spent(self, obj):
        return obj.get_total_spent()

    def get_days_since_last_wear(self, obj):
        return obj.get_days_since_last_wear()

    def get_restock_status(self, obj):
        return obj.get_restock_status()

    def get_cost_per_wear(self, obj):
        return obj.get_cost_per_wear()

    def get_is_low_comfort_high_cost(self, obj):
        return obj.is_low_comfort_high_cost()

    def get_purchase_records_count(self, obj):
        return obj.purchase_records.count()

    def get_active_restock_suggestions(self, obj):
        suggestions = obj.restock_suggestions.filter(is_dismissed=False, is_action_taken=False)[:3]
        return RestockSuggestionSerializer(suggestions, many=True).data

    def get_in_upcoming_travel(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        end_date = today + timedelta(days=90)
        return obj.travel_items.filter(
            travel_plan__start_date__gte=today,
            travel_plan__start_date__lte=end_date,
            travel_plan__status__in=['planning', 'upcoming']
        ).exists()

    def get_upcoming_travel_plans(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        end_date = today + timedelta(days=90)
        travel_items = obj.travel_items.filter(
            travel_plan__start_date__gte=today,
            travel_plan__start_date__lte=end_date,
            travel_plan__status__in=['planning', 'upcoming']
        ).select_related('travel_plan')[:5]
        plans = []
        for item in travel_items:
            tp = item.travel_plan
            plans.append({
                'id': tp.id,
                'name': tp.name,
                'destination': tp.destination,
                'start_date': tp.start_date.isoformat() if tp.start_date else None,
                'end_date': tp.end_date.isoformat() if tp.end_date else None,
                'role': item.get_role_display(),
                'quantity': item.quantity,
                'risk_level': tp.risk_level,
            })
        return plans


class PurchaseRecordSerializer(serializers.ModelSerializer):
    purchase_channel_display = serializers.CharField(source='get_channel_display_name', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    lens_brand = serializers.CharField(source='lens.brand', read_only=True, default='')
    lens_model = serializers.CharField(source='lens.model_name', read_only=True, default='')
    lens_color = serializers.CharField(source='lens.color', read_only=True, default='')

    class Meta:
        model = PurchaseRecord
        fields = '__all__'

    def create(self, validated_data):
        instance = super().create(validated_data)
        if instance.lens:
            instance.lens.stock_quantity += instance.quantity
            instance.lens.purchase_channel = instance.get_channel_display_name()
            instance.lens.unit_price = instance.unit_price
            instance.lens.discount = instance.discount
            instance.lens.shipping_fee = instance.shipping_fee
            instance.lens.total_paid = instance.actual_paid
            instance.lens.save()
        return instance

    def update(self, instance, validated_data):
        old_quantity = instance.quantity
        instance = super().update(instance, validated_data)
        if instance.lens and instance.quantity != old_quantity:
            instance.lens.stock_quantity += (instance.quantity - old_quantity)
            instance.lens.save()
        return instance


class RestockSuggestionSerializer(serializers.ModelSerializer):
    suggestion_type_display = serializers.CharField(source='get_suggestion_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    lens_brand = serializers.CharField(source='lens.brand', read_only=True)
    lens_model = serializers.CharField(source='lens.model_name', read_only=True, default='')
    lens_color = serializers.CharField(source='lens.color', read_only=True, default='')
    lens_id = serializers.IntegerField(source='lens.id', read_only=True)
    lens_remaining_stock = serializers.SerializerMethodField()
    lens_expiry_date = serializers.DateField(source='lens.expiry_date', read_only=True)

    class Meta:
        model = RestockSuggestion
        fields = '__all__'

    def get_lens_remaining_stock(self, obj):
        return obj.lens.get_remaining_stock() if obj.lens else 0


class BudgetStatsSerializer(serializers.Serializer):
    total_spent_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_spent_year = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_purchases_month = serializers.IntegerField()
    total_purchases_year = serializers.IntegerField()
    budget_month = serializers.CharField()
    budget_limit = serializers.DecimalField(max_digits=10, decimal_places=2)
    budget_used_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    is_over_budget = serializers.BooleanField()
    brand_spending = serializers.ListField()
    channel_spending = serializers.ListField()
    channel_price_comparison = serializers.ListField()
    monthly_trend = serializers.ListField()
    brand_value_ranking = serializers.ListField()
    low_comfort_high_cost = serializers.ListField()
    expiring_with_stock = serializers.ListField()
    running_out_soon = serializers.ListField()
    restock_suggestions = serializers.ListField()


class WearRecordSerializer(serializers.ModelSerializer):
    lens_brand = serializers.CharField(source='lens.brand', read_only=True, default='')
    lens_model = serializers.CharField(source='lens.model_name', read_only=True, default='')
    lens_color = serializers.CharField(source='lens.color', read_only=True, default='')
    outfit_plan = serializers.PrimaryKeyRelatedField(read_only=True, default=None)

    class Meta:
        model = WearRecord
        fields = '__all__'


class CareRecordSerializer(serializers.ModelSerializer):
    care_type_display = serializers.CharField(source='get_care_type_display', read_only=True)
    lens_brand = serializers.CharField(source='lens.brand', read_only=True)
    lens_model = serializers.CharField(source='lens.model_name', read_only=True)

    class Meta:
        model = CareRecord
        fields = '__all__'


class CareReminderSerializer(serializers.ModelSerializer):
    reminder_type_display = serializers.CharField(source='get_reminder_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    lens_brand = serializers.CharField(source='lens.brand', read_only=True)
    lens_model = serializers.CharField(source='lens.model_name', read_only=True)

    class Meta:
        model = CareReminder
        fields = '__all__'


class OutfitPlanSerializer(serializers.ModelSerializer):
    scene_name_display = serializers.CharField(source='get_scene_display_name', read_only=True)
    makeup_style_display = serializers.CharField(source='get_makeup_display_name', read_only=True)
    clothing_color_display = serializers.CharField(source='get_clothing_color_display', read_only=True)
    lighting_display = serializers.CharField(source='get_lighting_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    lens_brand = serializers.CharField(source='lens.brand', read_only=True, default='')
    lens_model = serializers.CharField(source='lens.model_name', read_only=True, default='')
    lens_color = serializers.CharField(source='lens.color', read_only=True, default='')

    backup_lens_brand = serializers.CharField(source='backup_lens.brand', read_only=True, default='')
    backup_lens_model = serializers.CharField(source='backup_lens.model_name', read_only=True, default='')

    wear_record_id = serializers.IntegerField(source='wear_record.id', read_only=True, allow_null=True)
    actual_duration_hours = serializers.FloatField(source='wear_record.duration_hours', read_only=True, allow_null=True)
    actual_comfort_level = serializers.IntegerField(source='wear_record.comfort_level', read_only=True, allow_null=True)

    duration_diff = serializers.SerializerMethodField()
    comfort_diff = serializers.SerializerMethodField()
    tag_labels = serializers.SerializerMethodField()

    class Meta:
        model = OutfitPlan
        fields = '__all__'

    def get_duration_diff(self, obj):
        return obj.get_duration_diff()

    def get_comfort_diff(self, obj):
        return obj.get_comfort_diff()

    def get_tag_labels(self, obj):
        tag_map = dict(OutfitPlan.TAG_CHOICES)
        return [{'key': tag, 'label': tag_map.get(tag, tag)} for tag in obj.tags or []]

    def create(self, validated_data):
        instance = super().create(validated_data)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if instance.wear_record:
            instance.update_tags()
            instance.save()
        return instance


class OutfitPlanStatsSerializer(serializers.Serializer):
    total_plans = serializers.IntegerField()
    pending_plans = serializers.IntegerField()
    completed_plans = serializers.IntegerField()
    cancelled_plans = serializers.IntegerField()
    avg_match_score = serializers.FloatField()
    top_makeup_styles = serializers.ListField()
    lens_usage_by_scene = serializers.ListField()
    match_score_ranking = serializers.ListField()
    upcoming_plans = serializers.ListField()
    tag_stats = serializers.DictField()


class TravelLensItemSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    lens_brand = serializers.CharField(source='lens.brand', read_only=True, default='')
    lens_model = serializers.CharField(source='lens.model_name', read_only=True, default='')
    lens_color = serializers.CharField(source='lens.color', read_only=True, default='')
    lens_status = serializers.CharField(source='lens.status', read_only=True, default='')
    lens_expiry_date = serializers.DateField(source='lens.expiry_date', read_only=True, default=None)
    lens_days_until_expiry = serializers.SerializerMethodField()
    lens_remaining_stock = serializers.SerializerMethodField()
    lens_avg_comfort = serializers.SerializerMethodField()
    lens_care_method = serializers.CharField(source='lens.care_method', read_only=True, default='')
    lens_open_date = serializers.DateField(source='lens.open_date', read_only=True, default=None)
    lens_is_under_rest = serializers.SerializerMethodField()

    class Meta:
        model = TravelLensItem
        fields = '__all__'
        extra_kwargs = {
            'travel_plan': {'read_only': True}
        }

    def get_lens_days_until_expiry(self, obj):
        return obj.lens.days_until_expiry() if obj.lens else None

    def get_lens_remaining_stock(self, obj):
        return obj.lens.get_remaining_stock() if obj.lens else 0

    def get_lens_avg_comfort(self, obj):
        return obj.lens.get_avg_comfort_level() if obj.lens else None

    def get_lens_is_under_rest(self, obj):
        return obj.lens.is_under_rest() if obj.lens else False


class TravelSupplyItemSerializer(serializers.ModelSerializer):
    supply_type_display = serializers.CharField(source='get_supply_display_name', read_only=True)

    class Meta:
        model = TravelSupplyItem
        fields = '__all__'
        extra_kwargs = {
            'travel_plan': {'read_only': True}
        }


class TravelDailyPlanSerializer(serializers.ModelSerializer):
    lens_brand = serializers.CharField(source='expected_wear_lens.brand', read_only=True, default='')
    lens_model = serializers.CharField(source='expected_wear_lens.model_name', read_only=True, default='')
    lens_color = serializers.CharField(source='expected_wear_lens.color', read_only=True, default='')

    class Meta:
        model = TravelDailyPlan
        fields = '__all__'
        extra_kwargs = {
            'travel_plan': {'read_only': True}
        }


class TravelRiskAlertSerializer(serializers.ModelSerializer):
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    related_lens_brand = serializers.CharField(source='related_lens.brand', read_only=True, default='')
    related_lens_model = serializers.CharField(source='related_lens.model_name', read_only=True, default='')

    class Meta:
        model = TravelRiskAlert
        fields = '__all__'
        extra_kwargs = {
            'travel_plan': {'read_only': True}
        }


class TravelPlanSerializer(serializers.ModelSerializer):
    climate_display = serializers.CharField(source='get_climate_display', read_only=True)
    transport_display = serializers.CharField(source='get_transport_display', read_only=True)
    luggage_display = serializers.CharField(source='get_luggage_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    planned_wear_scene_display = serializers.CharField(source='get_wear_scene_display_name', read_only=True)

    duration_days = serializers.SerializerMethodField()
    status_info = serializers.SerializerMethodField()
    total_lens_quantity = serializers.SerializerMethodField()
    primary_lens_count = serializers.SerializerMethodField()
    backup_lens_count = serializers.SerializerMethodField()
    supplies_checked_count = serializers.SerializerMethodField()
    supplies_total_count = serializers.SerializerMethodField()
    suggestions_and_risks = serializers.SerializerMethodField()
    active_risk_alerts = serializers.SerializerMethodField()

    lens_items = TravelLensItemSerializer(many=True, required=False)
    supplies = TravelSupplyItemSerializer(many=True, required=False)
    daily_plans = TravelDailyPlanSerializer(many=True, required=False)

    class Meta:
        model = TravelPlan
        fields = '__all__'

    def get_duration_days(self, obj):
        return obj.get_duration_days()

    def get_status_info(self, obj):
        return obj.get_status_info()

    def get_total_lens_quantity(self, obj):
        return sum(item.quantity for item in obj.lens_items.all())

    def get_primary_lens_count(self, obj):
        return obj.lens_items.filter(role='primary').count()

    def get_backup_lens_count(self, obj):
        return obj.lens_items.filter(role='backup').count()

    def get_supplies_checked_count(self, obj):
        return obj.supplies.filter(is_checked=True).count()

    def get_supplies_total_count(self, obj):
        return obj.supplies.count()

    def get_suggestions_and_risks(self, obj):
        suggestions, risks = obj.generate_suggestions_and_risks()
        return {'suggestions': suggestions, 'risks': risks}

    def get_active_risk_alerts(self, obj):
        alerts = obj.risk_alerts.filter(is_dismissed=False)
        return TravelRiskAlertSerializer(alerts, many=True).data

    def create(self, validated_data):
        lens_items_data = validated_data.pop('lens_items', [])
        supplies_data = validated_data.pop('supplies', [])
        daily_plans_data = validated_data.pop('daily_plans', [])

        travel_plan = TravelPlan.objects.create(**validated_data)
        travel_plan.update_auto_status()

        for item_data in lens_items_data:
            TravelLensItem.objects.create(travel_plan=travel_plan, **item_data)

        for supply_data in supplies_data:
            TravelSupplyItem.objects.create(travel_plan=travel_plan, **supply_data)

        for daily_data in daily_plans_data:
            TravelDailyPlan.objects.create(travel_plan=travel_plan, **daily_data)

        travel_plan.calculate_risk_level()
        return travel_plan

    def update(self, instance, validated_data):
        lens_items_data = validated_data.pop('lens_items', None)
        supplies_data = validated_data.pop('supplies', None)
        daily_plans_data = validated_data.pop('daily_plans', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.update_auto_status()

        if lens_items_data is not None:
            instance.lens_items.all().delete()
            for item_data in lens_items_data:
                TravelLensItem.objects.create(travel_plan=instance, **item_data)

        if supplies_data is not None:
            instance.supplies.all().delete()
            for supply_data in supplies_data:
                TravelSupplyItem.objects.create(travel_plan=instance, **supply_data)

        if daily_plans_data is not None:
            instance.daily_plans.all().delete()
            for daily_data in daily_plans_data:
                TravelDailyPlan.objects.create(travel_plan=instance, **daily_data)

        instance.calculate_risk_level()
        return instance


class TravelStatsSerializer(serializers.Serializer):
    total_plans = serializers.IntegerField()
    completed_plans = serializers.IntegerField()
    upcoming_plans = serializers.IntegerField()
    in_progress_plans = serializers.IntegerField()
    high_risk_count = serializers.IntegerField()
    medium_risk_count = serializers.IntegerField()
    low_risk_count = serializers.IntegerField()
    total_travel_days = serializers.IntegerField()
    total_lens_used_in_travel = serializers.IntegerField()
    lens_travel_usage_ranking = serializers.ListField()
    travel_comfort_ranking = serializers.ListField()
    travel_risk_count = serializers.IntegerField()
    common_supplies = serializers.ListField()
    destination_stats = serializers.ListField()
    climate_stats = serializers.ListField()
    recent_travel_plans = serializers.ListField()
    total_risk_alerts = serializers.IntegerField()
    dismissed_risk_alerts = serializers.IntegerField()
    active_risk_alerts = serializers.IntegerField()
    status_counts = serializers.DictField()
    risk_counts = serializers.DictField()
    lens_usage_ranking = serializers.ListField()
    comfort_ranking = serializers.ListField()
    total_alerts = serializers.IntegerField()
    alert_type_stats = serializers.DictField()
