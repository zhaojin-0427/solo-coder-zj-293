from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LensViewSet, WearRecordViewSet, StatsViewSet

router = DefaultRouter()
router.register(r'lenses', LensViewSet, basename='lens')
router.register(r'records', WearRecordViewSet, basename='wearrecord')
router.register(r'stats', StatsViewSet, basename='stats')

urlpatterns = [
    path('', include(router.urls)),
]
