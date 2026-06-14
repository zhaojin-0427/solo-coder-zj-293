from rest_framework import serializers
from django.db.models import Sum, Avg, Count
from .models import Lens, WearRecord, CareRecord, CareReminder, OutfitPlan, PurchaseRecord, RestockSuggestion


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
