from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LensViewSet, WearRecordViewSet, StatsViewSet,
    CareRecordViewSet, CareReminderViewSet
)

router = DefaultRouter()
router.register(r'lenses', LensViewSet, basename='lens')
router.register(r'records', WearRecordViewSet, basename='wearrecord')
router.register(r'stats', StatsViewSet, basename='stats')
router.register(r'care-records', CareRecordViewSet, basename='carerecord')
router.register(r'care-reminders', CareReminderViewSet, basename='carereminder')

urlpatterns = [
    path('', include(router.urls)),
]
