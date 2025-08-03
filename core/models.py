from django.contrib.auth.models import User
from django.db import models

import constants
from core.model_metrics import MetricsModelMixin


class TimeStampMixin(models.Model):
    """
    TimeStamp Mixin
    Abstract model with created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Vendor(MetricsModelMixin, models.Model):
    """
    Model for vendor user account
    Vendor has access to CRUD Phone Numbers also, vendor has balance and can charge Phone Numbers.
    Total sell is the total number of credits sold to phone numbers by vendor
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.PositiveIntegerField(default=0)
    total_sell = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.username


class PhoneNumber(MetricsModelMixin, models.Model):
    """
    Model for phone number.
    Phone number has balance and can charge by vendor.
    """
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='phone_numbers')
    phone_number = models.CharField(max_length=255, unique=True)
    balance = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.phone_number


# =============================================================================
# There is several approach to implement transactions.
#
# 1- Polymorphic model:
# It is recommended to use this approach.
# Unfortunately it is not available in Django itself, You can use Django Polymorphic package.
# (Not Support Django 5.x)
#
# https://django-polymorphic.readthedocs.io/en/stable/
# "The current release of django-polymorphic supports Django 2.2 - 4.0 and Python 3.6+."
#
# 2- Abstract model:
# Do not need any package for it. Can be used with Django itself.
# Better for clean code, but it is not recommended for production because it is not efficient in queries.
# For filtering all Phone Number transactions and Vendor transactions, we need to use two different queries.
# But it is a good option for development with Django 5.x
#
# 3- Nullable Fields in Transaction Model:
# There is a big problem with this approach.
# It is not recommended because there are a lot of nullable fields that we need one of them in an instance.
# =============================================================================

class BaseTransaction(TimeStampMixin):
    """
    Base polymorphic transaction model.
    """
    amount = models.PositiveIntegerField()
    state = models.CharField(max_length=20, choices=constants.TRANSACTION_STATE)

    class Meta:
        abstract = True


class VendorTransaction(MetricsModelMixin, BaseTransaction):
    """
    Transactions related to vendor.
    """
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='vendor_transactions')
    reject_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"[Vendor Transaction] {self.vendor.user.username} - {self.amount} - {self.state}"


class PhoneNumberTransaction(MetricsModelMixin, BaseTransaction):
    """
    Transactions related to phone number.
    """
    phone_number = models.ForeignKey(PhoneNumber, on_delete=models.CASCADE, related_name='phone_number_transactions')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='phone_transactions')

    def __str__(self):
        return f"[PhoneNumber Transaction] {self.phone_number.phone_number} - {self.amount} - {self.state}"
