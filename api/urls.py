from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    LoginAPIView, MeAPIView, BranchViewSet, StaffProfileViewSet, ProductViewSet, ProductPackingSizeViewSet,
    ProductMarginViewSet,VehicleViewSet,ExpenseViewSet

)

router = DefaultRouter()
router.register(r'branches', BranchViewSet)
router.register(r'staff', StaffProfileViewSet)
router.register(r'products', ProductViewSet)
router.register(r'product-packing-sizes', ProductPackingSizeViewSet)
router.register(r'product-margins', ProductMarginViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'expenses', ExpenseViewSet)

urlpatterns = [
    path('auth/login/', LoginAPIView.as_view(), name='api_login'),
    path('auth/me/', MeAPIView.as_view(), name='api_me'),
    path('', include(router.urls)),
]

