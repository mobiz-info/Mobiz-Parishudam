from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    LoginAPIView, MeAPIView, BranchViewSet, StaffProfileViewSet
)

router = DefaultRouter()
router.register(r'branches', BranchViewSet)
router.register(r'staff', StaffProfileViewSet)

urlpatterns = [
    path('auth/login/', LoginAPIView.as_view(), name='api_login'),
    path('auth/me/', MeAPIView.as_view(), name='api_me'),
    path('', include(router.urls)),
]

