from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from psycopg2 import IntegrityError
from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

import constants
from core.cache import CacheMixin, cache_get, cache_set
from core.models import Vendor, VendorTransaction, PhoneNumber, PhoneNumberTransaction
from .permissions import IsVendorUser
from .serializers import (
    VendorSerializer, VendorTransactionSerializer,
    UserUpdateSerializer,
    UserSerializer, VendorUpdateSerializer, PhoneNumberSerializer,
    VendorTransactionUpdateSerializer, PhoneNumberTransactionSerializer
)


class AdminUserViewSet(CacheMixin, viewsets.ModelViewSet):
    queryset = User.objects.filter(is_staff=True)
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return UserSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(is_staff=True)


class VendorViewSet(CacheMixin, viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return VendorUpdateSerializer
        return VendorSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        user_data = serializer.validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        serializer.save(user=user)

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.instance
        user_data = serializer.validated_data.pop('user', None)
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance):
        user = instance.user
        instance.delete()
        user.delete()

    @action(detail=False, methods=['get'], permission_classes=[IsVendorUser])
    def me(self, request):
        vendor = Vendor.objects.get(user=request.user)
        serializer = VendorSerializer(vendor)
        return Response(serializer.data)


class PhoneNumberViewSet(CacheMixin, viewsets.ModelViewSet):
    serializer_class = PhoneNumberSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            perm_cls = permissions.IsAdminUser | IsVendorUser
        else:
            perm_cls = IsVendorUser
        return [perm_cls()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return PhoneNumber.objects.none()
        if user.is_staff:
            return PhoneNumber.objects.all()
        return PhoneNumber.objects.filter(vendor__user=user)

    def perform_create(self, serializer):
        vendor = Vendor.objects.get(user=self.request.user)
        serializer.save(vendor=vendor)


class VendorTransactionViewSet(
    CacheMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    http_method_names = ['get', 'post']

    permissions_dict = {
        'list': permissions.IsAdminUser | IsVendorUser,
        'retrieve': permissions.IsAdminUser | IsVendorUser,
        'create': IsVendorUser,
        'change_state': permissions.IsAdminUser,
    }

    def get_permissions(self):
        perm = self.permissions_dict.get(self.action)
        return [perm()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return VendorTransaction.objects.none()
        if user.is_staff:
            return VendorTransaction.objects.all()
        return VendorTransaction.objects.filter(vendor__user=user)

    def get_serializer_class(self):
        if self.action == 'change_state':
            return VendorTransactionUpdateSerializer
        return VendorTransactionSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        vendor = Vendor.objects.get(user=self.request.user)
        serializer.save(vendor=vendor, state=constants.PENDING)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def change_state(self, request, pk=None):
        with transaction.atomic():
            vendor_transaction = (
                VendorTransaction.objects
                .select_for_update()
                .select_related('vendor')
                .get(pk=pk)
            )
            serializer = VendorTransactionUpdateSerializer(
                vendor_transaction,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            if vendor_transaction.state != constants.PENDING:
                return Response({'detail': 'Transaction is not pending'}, status=status.HTTP_400_BAD_REQUEST)
            new_state = serializer.validated_data.get('state', vendor_transaction.state)
            vendor = Vendor.objects.select_for_update().get(pk=vendor_transaction.vendor.pk)
            vendor_transaction.state = new_state
            vendor_transaction.reject_reason = serializer.validated_data.get('reject_reason', '')
            vendor_transaction.save(update_fields=['state', 'reject_reason', 'updated_at'])
            if new_state == constants.APPROVED:
                vendor.balance = F('balance') + vendor_transaction.amount
                vendor.save(update_fields=['balance'])
                vendor.refresh_from_db(fields=['balance'])
        response_data = VendorTransactionUpdateSerializer(vendor_transaction).data
        response_data['vendor'] = VendorSerializer(vendor).data
        self.invalidate_related_caches(vendor_transaction.vendor)
        self.invalidate_related_caches(vendor_transaction)
        return Response(response_data, status=status.HTTP_200_OK)


class PhoneNumberTransactionViewSet(
    CacheMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    http_method_names = ['get', 'post']
    serializer_class = PhoneNumberTransactionSerializer
    permissions_dict = {
        'list': permissions.IsAdminUser | IsVendorUser,
        'retrieve': permissions.IsAdminUser | IsVendorUser,
        'create': IsVendorUser,
    }

    def get_permissions(self):
        perm = self.permissions_dict.get(self.action)
        return [perm()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return PhoneNumberTransaction.objects.none()

        if user.is_staff:
            return PhoneNumberTransaction.objects.all()
        return PhoneNumberTransaction.objects.filter(vendor__user=user)

    @transaction.atomic
    def perform_create(self, serializer):
        vendor = Vendor.objects.select_for_update().get(user=self.request.user)
        phone_number = PhoneNumber.objects.select_for_update().get(
            pk=serializer.validated_data['phone_number'].pk,
            vendor=vendor
        )
        amount = serializer.validated_data['amount']

        try:
            vendor.balance = F('balance') - amount
            vendor.total_sell = F('total_sell') + amount
            vendor.save(update_fields=['balance', 'total_sell'])

            phone_number.balance = F('balance') + amount
            phone_number.save(update_fields=['balance'])

            vendor.refresh_from_db(fields=['balance', 'total_sell'])
            phone_number.refresh_from_db(fields=['balance'])

            serializer.save(
                vendor=vendor,
                phone_number=phone_number,
                state=constants.APPROVED
            )
        except IntegrityError:
            raise ValidationError("Insufficient balance or transaction conflict.")
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_409_CONFLICT)


class CachedTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        cache_key = f"jwt_token_{request.data.get('username')}"
        cached_response = cache_get(cache_key)
        if cached_response:
            return Response(cached_response)

        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            cache_set(cache_key, response.data, timeout=60)
        return response
