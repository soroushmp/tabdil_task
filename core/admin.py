from django.contrib import admin

from core.models import Vendor, PhoneNumber, VendorTransaction, PhoneNumberTransaction


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'total_sell']


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'vendor', 'balance']


@admin.register(VendorTransaction)
class VendorTransactionAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'amount', 'state', 'created_at', 'updated_at', 'reject_reason']


@admin.register(PhoneNumberTransaction)
class PhoneNumberTransactionAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'phone_number', 'amount', 'state', 'created_at', 'updated_at']
