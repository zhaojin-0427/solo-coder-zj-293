from django.contrib import admin
from .models import Lens, WearRecord


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
