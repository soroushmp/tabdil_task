from rest_framework import permissions
from core.models import Vendor


class IsVendorUser(permissions.BasePermission):
    """
    Custom permission to only allow users who have an associated vendor account.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Check if the authenticated user has an associated vendor
        return Vendor.objects.filter(user=request.user).exists()
