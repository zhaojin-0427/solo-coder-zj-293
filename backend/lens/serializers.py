from rest_framework import serializers
from django.db.models import Sum, Avg
from .models import Lens, WearRecord


class LensSerializer(serializers.ModelSerializer):
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    daily_wear_limit = serializers.SerializerMethodField()
    total_wear_hours = serializers.SerializerMethodField()
    last_wear_date = serializers.SerializerMethodField()
    avg_comfort = serializers.SerializerMethodField()

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


class WearRecordSerializer(serializers.ModelSerializer):
    lens_brand = serializers.CharField(source='lens.brand', read_only=True)
    lens_model = serializers.CharField(source='lens.model_name', read_only=True)
    lens_color = serializers.CharField(source='lens.color', read_only=True)

    class Meta:
        model = WearRecord
        fields = '__all__'
