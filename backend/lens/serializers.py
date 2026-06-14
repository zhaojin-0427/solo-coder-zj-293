from rest_framework import serializers
from django.db.models import Sum, Avg, Count
from .models import Lens, WearRecord, CareRecord, CareReminder, OutfitPlan


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
