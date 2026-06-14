from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LensViewSet, WearRecordViewSet, StatsViewSet,
    CareRecordViewSet, CareReminderViewSet, OutfitPlanViewSet
)

router = DefaultRouter()
router.register(r'lenses', LensViewSet, basename='lens')
router.register(r'records', WearRecordViewSet, basename='wearrecord')
router.register(r'stats', StatsViewSet, basename='stats')
router.register(r'care-records', CareRecordViewSet, basename='carerecord')
router.register(r'care-reminders', CareReminderViewSet, basename='carereminder')
router.register(r'outfit-plans', OutfitPlanViewSet, basename='outfitplan')

urlpatterns = [
    path('', include(router.urls)),
]
