from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AdminUserViewSet, VendorViewSet, VendorTransactionViewSet,
    PhoneNumberViewSet, PhoneNumberTransactionViewSet
)

router = DefaultRouter()
router.register('admin-users', AdminUserViewSet, basename='admin-users')
router.register('vendors', VendorViewSet, basename='vendors')
router.register('vendor-transactions', VendorTransactionViewSet, basename='vendor-transactions')
router.register('phone-numbers', PhoneNumberViewSet, basename='phone-numbers')
router.register('phone-transactions', PhoneNumberTransactionViewSet, basename='phone-transactions')

urlpatterns = [
    path('', include(router.urls)),
]
