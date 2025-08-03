from django.contrib.auth.models import User
from django.test import TransactionTestCase
from rest_framework.test import APITestCase

import constants
from core.models import Vendor, PhoneNumber, VendorTransaction, PhoneNumberTransaction


class BaseAPITestCase(APITestCase):
    def create_admin(self):
        return User.objects.create_user(username='admin', password='adminpass', is_staff=True)

    def create_vendor_user(self):
        user = User.objects.create_user(username='vendor', password='vendorpass')
        vendor = Vendor.objects.create(user=user, balance=1000, total_sell=0)
        return user, vendor


class AdminUserViewSetTest(BaseAPITestCase):
    def test_create_admin_user(self):
        admin = self.create_admin()
        self.client.force_authenticate(admin)
        data = {"username": "newadmin", "password": "pass123"}
        response = self.client.post("/api/admin-users/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.get(username="newadmin").is_staff)


class VendorViewSetTest(BaseAPITestCase):
    def setUp(self):
        self.admin = self.create_admin()
        self.client.force_authenticate(self.admin)

    def test_create_vendor(self):
        data = {"user": {"username": "vendorA", "password": "vendorpass"}}
        response = self.client.post("/api/vendors/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="vendorA").exists())
        self.assertTrue(Vendor.objects.filter(user__username="vendorA").exists())

    def test_update_vendor_and_user(self):
        user, vendor = self.create_vendor_user()
        data = {"user": {"username": "updatedvendor"}}
        response = self.client.patch(f"/api/vendors/{vendor.id}/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.username, "updatedvendor")

    def test_delete_vendor_also_deletes_user(self):
        user, vendor = self.create_vendor_user()
        response = self.client.delete(f"/api/vendors/{vendor.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=user.id).exists())

    def test_vendor_me_endpoint(self):
        user, vendor = self.create_vendor_user()
        self.client.force_authenticate(user)
        response = self.client.get("/api/vendors/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], vendor.id)


class PhoneNumberViewSetTest(BaseAPITestCase):
    def test_vendor_can_create_phone_number(self):
        user, vendor = self.create_vendor_user()
        self.client.force_authenticate(user)
        data = {"phone_number": "1234567890", "balance": 0}  # no vendor here
        response = self.client.post("/api/phone-numbers/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PhoneNumber.objects.filter(phone_number="1234567890", vendor=vendor).exists())


class VendorTransactionViewSetTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()

    def create_vendor_user(self):
        user = User.objects.create_user(username='vendor', password='vendorpass')
        vendor = Vendor.objects.create(user=user, balance=1000, total_sell=0)
        return user, vendor

    def create_admin(self):
        return User.objects.create_user(username='admin', password='adminpass', is_staff=True)

    def test_vendor_can_create_transaction(self):
        user, vendor = self.create_vendor_user()
        self.client.force_authenticate(user)
        data = {"amount": 500}
        response = self.client.post("/api/vendor-transactions/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        tx = VendorTransaction.objects.get(vendor=vendor)
        self.assertEqual(tx.state, constants.PENDING)

    def test_admin_can_change_state_to_approved_and_balance_updates(self):
        user, vendor = self.create_vendor_user()
        tx = VendorTransaction.objects.create(vendor=vendor, amount=200, state=constants.PENDING)
        admin = self.create_admin()
        self.client.force_authenticate(admin)
        data = {"state": constants.APPROVED}
        response = self.client.post(f"/api/vendor-transactions/{tx.id}/change_state/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        vendor.refresh_from_db()
        self.assertEqual(vendor.balance, 1200)

    def test_concurrent_approvals_only_one_updates_balance(self):
        user, vendor = self.create_vendor_user()
        tx = VendorTransaction.objects.create(vendor=vendor, amount=200, state=constants.PENDING)
        admin1 = self.create_admin()
        admin2 = User.objects.create_user(username='admin2', password='adminpass', is_staff=True)

        def approve_transaction_as_admin(admin_user, results, index):
            try:
                client = APIClient()
                client.force_authenticate(admin_user)
                data = {"state": constants.APPROVED}
                response = client.post(f"/api/vendor-transactions/{tx.id}/change_state/", data, format='json')
                results[index] = response.status_code
            finally:
                connection.close()

        results = [None, None]
        t1 = threading.Thread(target=approve_transaction_as_admin, args=(admin1, results, 0))
        t2 = threading.Thread(target=approve_transaction_as_admin, args=(admin2, results, 1))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        vendor.refresh_from_db()
        approved_count = VendorTransaction.objects.filter(state=constants.APPROVED).count()
        self.assertEqual(approved_count, 1)
        self.assertEqual(vendor.balance, 1200)
        self.assertIn(status.HTTP_200_OK, results)
        self.assertIn(status.HTTP_400_BAD_REQUEST, results)


class PhoneNumberTransactionViewSetTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()

    def create_vendor_user(self):
        user = User.objects.create_user(username='vendor', password='vendorpass')
        vendor = Vendor.objects.create(user=user, balance=1000, total_sell=0)
        return user, vendor

    def test_vendor_can_transfer_balance_to_phone_number(self):
        user, vendor = self.create_vendor_user()
        phone = PhoneNumber.objects.create(vendor=vendor, phone_number="55555", balance=0)
        self.client.force_authenticate(user=user)
        data = {"phone_number": phone.id, "amount": 100}
        response = self.client.post("/api/phone-transactions/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        vendor.refresh_from_db()
        phone.refresh_from_db()
        self.assertEqual(vendor.balance, 900)
        self.assertEqual(phone.balance, 100)


from django.db import connection
from django.db.models import F
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TransactionTestCase
import threading


class VendorMassiveTransactionTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()
        self.vendor_users = []
        self.vendors = []
        self.phones = []

        for i in range(2):
            user = User.objects.create_user(username=f'vendor{i}', password='pass')
            vendor = Vendor.objects.create(user=user, balance=0, total_sell=0)
            phone = PhoneNumber.objects.create(vendor=vendor, phone_number=f'55555{i}', balance=0)
            self.vendor_users.append(user)
            self.vendors.append(vendor)
            self.phones.append(phone)

    def test_massive_topup_and_sales(self):
        topup_amount = 1000
        sales_amount = 1

        # Perform 10 top-ups for each vendor
        for idx, vendor in enumerate(self.vendors):
            for _ in range(10):
                Vendor.objects.filter(pk=vendor.pk).update(balance=F('balance') + topup_amount)
            vendor.refresh_from_db()

        # Function to perform sales (transfer balance to phone)
        def perform_sales(user, phone, results, index):
            try:
                client = APIClient()
                client.force_authenticate(user)
                for _ in range(500):  # 500 sales for each vendor
                    data = {"phone_number": phone.id, "amount": sales_amount}
                    response = client.post("/api/phone-transactions/", data, format='json')
                    results[index].append(response.status_code)
            finally:
                connection.close()  # Ensure DB connection closes in each thread

        results = [[] for _ in range(2)]
        threads = [
            threading.Thread(target=perform_sales, args=(self.vendor_users[0], self.phones[0], results, 0)),
            threading.Thread(target=perform_sales, args=(self.vendor_users[1], self.phones[1], results, 1)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for vendor in self.vendors:
            vendor.refresh_from_db()
        for phone in self.phones:
            phone.refresh_from_db()

        # Each vendor topup = 10 * 1000 = 10000
        # Each vendor made 500 sales * 1 = 500 deducted
        self.assertEqual(self.vendors[0].balance, 10000 - 500)
        self.assertEqual(self.vendors[1].balance, 10000 - 500)

        # Each phone receives 500 units
        self.assertEqual(self.phones[0].balance, 500)
        self.assertEqual(self.phones[1].balance, 500)

        # Verify total transactions
        total_transactions = PhoneNumberTransaction.objects.count()
        self.assertEqual(total_transactions, 1000)

        # Ensure all requests succeeded
        for res_list in results:
            self.assertTrue(all(status == 201 for status in res_list))
