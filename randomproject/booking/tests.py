from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from .models import Receipt, Company, Address
from django.utils import timezone
from datetime import timedelta
import math

User = get_user_model()
abs_tol = 0.02  # used for math.isclose() function


class BookingTestCase(APITestCase):

    def setUp(self):
        self.user_data = {
            "username": "TestUser",
            "email": "test@test.com",
            "first_name": "Test",
            "last_name": "Test",
            "phone": "123456789",
            "date_of_birth": "2020-04-04",
            "password1": "testpassword123",
            "password2": "testpassword123"
        }

        register_response = self.client.post(reverse("rest_register"), self.user_data, format="json")
        access_token = register_response.data['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.company_data = {
            "name": "TestCompany",
            "website": "test.com",
            "company_address": {
                "street": "Teststreet",
                "building_number": 12,
                "post_code": "12-345",
                "city": "TestCity",
                "country": "Poland"
            },
            "nip_number": 1234567890
        }

        self.client.post(reverse("company-list"), self.company_data, format="json")

        self.receipt_data = {
            "header": "Thank you for supporting our shop",
            "company_name": "TestCompany",
            "currency": "PLN",
            "checkout_number": 5,
            "products": [
                {
                    "name": "Egg",
                    "unit_price": 1,
                    "quantity": 5,
                    "vat_type": "A"
                },
                {
                    "name": "Apple",
                    "unit_price": 0.95,
                    "quantity": 100,
                    "vat_type": "B"
                }
            ]
        }

        self.invoice_data = {
            "company_name": "TestCompany",
            "buyer_address": {
                "street": "Teststreet",
                "building_number": 12,
                "post_code": "12-345",
                "city": "TestCity",
                "country": "Poland"
            },
            "buyer_name": "TestBuyer",
            "buyer_nip": "1234567890",
            "date_finished": "2020-01-01",
            "products": [
                {
                    "name": "Shelf",
                    "unit_price": 4.99,
                    "unit": "pcs",
                    "quantity": 10,
                    "vat_tax": 23
                },
                {
                    "name": "Kettle",
                    "unit_price": 10.99,
                    "unit": "pcs",
                    "quantity": 2,
                    "vat_tax": 23
                }
            ],
            "currency": "EUR",
            "is_paid": True
        }

    def test_create_company_with_existing_name(self):
        response = self.client.post(reverse("company-list"), self.company_data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_user_cannot_edit_others_company(self):
        new_user = User.objects.create(
            username="otheruser",
            first_name="other",
            last_name="user",
            date_of_birth="1999-01-01",
            phone=999999999
        )
        address = Address.objects.get()
        company_data = self.company_data.copy()
        company_data['name'] = "OtherCompany"
        del company_data['company_address']
        Company.objects.create(**company_data, company_address=address, owner=new_user)
        response = self.client.patch(
            reverse("company-detail", kwargs={"name": "OtherCompany"}),
            {"nip_number": 1111111111},
            format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_create_receipt(self):
        receipt_response = self.client.post(
            reverse("receipt-list"),
            self.receipt_data,
            format="json"
        )
        self.assertEqual(receipt_response.status_code, 201)
        gross_price = float(receipt_response.data['gross_price'])
        self.assertTrue(math.isclose(gross_price, round(0.95 * 100 + 1 * 5, 2), abs_tol=abs_tol))
        tax_a = round((1 - 1 / 1.23) * 5, 2)
        tax_b = round((0.95 - 0.95 / 1.08) * 100, 2)
        total_tax = tax_a + tax_b
        self.assertTrue(math.isclose(float(receipt_response.data['tax_values']['B']), tax_b, abs_tol=abs_tol))
        self.assertTrue(math.isclose(float(receipt_response.data['total_tax']), total_tax, abs_tol=abs_tol))

    def test_user_invalid_company_name(self):
        receipt_data = self.receipt_data.update(company_name="Doesnt exist")
        response = self.client.post(reverse("receipt-list"), receipt_data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_print_numbers(self):
        response = self.client.post(reverse("receipt-list"), self.receipt_data, format="json")
        print_number = response.data['print_number']
        for _ in range(5):
            response = self.client.post(reverse("receipt-list"), self.receipt_data, format="json")
        self.assertEqual(response.data['print_number'], print_number + 5)
        Receipt.objects.all().update(date_created=timezone.now()-timedelta(days=2))
        response = self.client.post(reverse("receipt-list"), self.receipt_data, format="json")
        self.assertEqual(response.data['print_number'], 1)

    def test_create_invoice(self):
        response = self.client.post(reverse("invoice-list"), self.invoice_data, format="json")
        self.assertEqual(response.status_code, 201)
        products = self.invoice_data['products']
        calculated_tax = 0
        net_price = 0
        for product in products:
            calculated_tax += product['unit_price'] * (product['vat_tax'] / 100) * product['quantity']
            net_price += product['unit_price'] * product['quantity']
        calculated_tax = round(calculated_tax, 2)
        gross_price = round(net_price + calculated_tax, 2)
        self.assertTrue(math.isclose(float(response.data['total_tax']), calculated_tax, abs_tol=abs_tol))
        self.assertTrue(math.isclose(float(response.data['net_price']), net_price, abs_tol=abs_tol))
        self.assertTrue(math.isclose(float(response.data['gross_price']), gross_price, abs_tol=abs_tol))
