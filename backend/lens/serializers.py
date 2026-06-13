from rest_framework import serializers
from django.db.models import Sum, Avg, Count
from .models import Lens, WearRecord, CareRecord, CareReminder


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
