from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LensViewSet, WearRecordViewSet, StatsViewSet,
    CareRecordViewSet, CareReminderViewSet, OutfitPlanViewSet,
    PurchaseRecordViewSet, RestockSuggestionViewSet, BudgetViewSet,
    TravelPlanViewSet, TravelLensItemViewSet, TravelSupplyItemViewSet,
    TravelDailyPlanViewSet, TravelRiskAlertViewSet
)

router = DefaultRouter()
router.register(r'lenses', LensViewSet, basename='lens')
router.register(r'records', WearRecordViewSet, basename='wearrecord')
router.register(r'stats', StatsViewSet, basename='stats')
router.register(r'care-records', CareRecordViewSet, basename='carerecord')
router.register(r'care-reminders', CareReminderViewSet, basename='carereminder')
router.register(r'outfit-plans', OutfitPlanViewSet, basename='outfitplan')
router.register(r'purchase-records', PurchaseRecordViewSet, basename='purchaserecord')
router.register(r'restock-suggestions', RestockSuggestionViewSet, basename='restocksuggestion')
router.register(r'budget', BudgetViewSet, basename='budget')
router.register(r'travel-plans', TravelPlanViewSet, basename='travelplan')
router.register(r'travel-lens-items', TravelLensItemViewSet, basename='travellensitem')
router.register(r'travel-supply-items', TravelSupplyItemViewSet, basename='travelsupplyitem')
router.register(r'travel-daily-plans', TravelDailyPlanViewSet, basename='traveldailyplan')
router.register(r'travel-risk-alerts', TravelRiskAlertViewSet, basename='travelriskalert')

urlpatterns = [
    path('', include(router.urls)),
]
