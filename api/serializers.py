from django.contrib.auth.models import User
from rest_framework import serializers

import constants
from core.models import Vendor, VendorTransaction, PhoneNumber, PhoneNumberTransaction


# Serializers

# -- User --
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {'default': 'admin'},
            'email': {'default': 'admin@localhost'},
            'password': {'default': 'admin', 'write_only': True},
        }


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {'default': 'admin'},
            'email': {'default': 'admin@localhost'},
        }


# -- Vendor User --
class VendorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Vendor
        fields = ['id', 'user', 'balance', 'total_sell']
        extra_kwargs = {
            'id': {'read_only': True},
            'balance': {'read_only': True},
            'total_sell': {'read_only': True},
        }


class VendorUpdateSerializer(serializers.ModelSerializer):
    user = UserUpdateSerializer()

    class Meta:
        model = Vendor
        fields = ['id', 'user', 'balance', 'total_sell']
        extra_kwargs = {
            'id': {'read_only': True},
            'balance': {'read_only': True},
            'total_sell': {'read_only': True},
        }


# -- Phone Number --
class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ['id', 'phone_number', 'balance', 'vendor']
        extra_kwargs = {
            'id': {'read_only': True},
            'phone_number': {'default': '09123456789'},
            'balance': {'read_only': True},
            'vendor': {'read_only': True},
        }


# -- Vendor Transaction --
class VendorTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorTransaction
        fields = ['id', 'amount', 'state', 'vendor', 'reject_reason']
        extra_kwargs = {
            'id': {'read_only': True},
            'amount': {'default': 1000},
            'state': {'read_only': True},
            'vendor': {'read_only': True},
            'reject_reason': {'read_only': True},
        }

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value


class VendorTransactionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorTransaction
        fields = ['state', 'reject_reason']
        extra_kwargs = {
            'state': {'default': constants.APPROVED},
            'reject_reason': {'default': '', 'required': False},
        }


class PhoneNumberTransactionSerializer(serializers.ModelSerializer):
    phone_number = serializers.PrimaryKeyRelatedField(queryset=PhoneNumber.objects.all())

    class Meta:
        model = PhoneNumberTransaction
        fields = ['id', 'amount', 'state', 'vendor', 'phone_number']
        extra_kwargs = {
            'id': {'read_only': True},
            'amount': {'default': 1000},
            'state': {'read_only': True},
            'vendor': {'read_only': True},
        }

    def validate(self, attrs):
        request = self.context['request']
        vendor = Vendor.objects.filter(user=request.user).first()

        phone_number = attrs['phone_number']
        if phone_number.vendor != vendor:
            raise serializers.ValidationError("Phone number is not owned by this vendor.")

        amount = attrs['amount']
        if vendor.balance < amount:
            raise serializers.ValidationError("Insufficient balance.")

        if amount <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")

        attrs['vendor'] = vendor
        return attrs
