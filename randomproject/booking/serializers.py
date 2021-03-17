from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import ReceiptProduct, Address, Receipt, Company, InvoiceProduct, Invoice
from collections import defaultdict
from django.utils import timezone


class ReceiptProductSerializer(serializers.ModelSerializer):

    def validate_vat_type(self, vat_type):
        if vat_type.upper() not in "ABCDE":
            raise ValidationError("Invalid vat type, must be either A, B, C, D or E")
        return vat_type.upper()

    def get_price(self, product):
        return round(product.quantity * product.unit_price, 2)

    def get_total_discount_value(self, product):
        return round(product.quantity * product.discount_value, 2)

    def get_full_price(self, product):
        return round(product.quantity * (product.unit_price - product.discount_value), 2)

    price = serializers.SerializerMethodField("get_price")
    total_discount_value = serializers.SerializerMethodField("get_total_discount_value")
    full_price = serializers.SerializerMethodField("get_full_price")

    class Meta:
        model = ReceiptProduct
        exclude = ("receipt",)


class InvoiceProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvoiceProduct
        exclude = ("invoice",)

    price = serializers.SerializerMethodField("get_price")
    total_discount_value = serializers.SerializerMethodField("get_total_discount_value")
    full_price = serializers.SerializerMethodField("get_full_price")

    def get_price(self, product):
        return round(product.unit_price * product.quantity, 2)

    def get_total_discount_value(self, product):
        return round(product.quantity * product.discount_value, 2)

    def get_full_price(self, product):
        return round(product.quantity * (product.unit_price - product.discount_value), 2)


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = "__all__"


class CompanySerializer(serializers.ModelSerializer):

    company_address = AddressSerializer()

    class Meta:
        model = Company
        exclude = ("owner",)

    def validate_nip_number(self, nip_number):
        if not nip_number.isnumeric() or len(nip_number) != 10:
            raise ValidationError("Invalid NIP number")
        return nip_number

    def create(self, validated_data):
        user = self.context['request'].user
        address = validated_data.pop("company_address")
        company_address = Address.objects.create(**address)
        company = Company.objects.create(**validated_data, owner=user, company_address=company_address)
        return company

    def update(self, instance, validated_data):
        address = validated_data.pop("company_address")
        with transaction.atomic():
            if address is not None:
                company_address = instance.company_address
                for name, value in address.items():
                    setattr(company_address, name, value)
                company_address.save()
            for name, value in validated_data.items():
                setattr(instance, name, value)
            instance.save()
        return instance


class ReceiptSerializer(serializers.ModelSerializer):

    company = CompanySerializer(read_only=True)
    company_name = serializers.CharField(max_length=150, write_only=True)
    products = ReceiptProductSerializer(many=True)
    total_price = serializers.SerializerMethodField("get_total_price")
    tax_values = serializers.SerializerMethodField("get_tax_values")
    total_tax = serializers.SerializerMethodField("get_total_tax")

    def validate_products(self, products):
        if not len(products):
            raise ValidationError("This field is required.")
        return products

    def create(self, validated_data):
        products = validated_data.pop("products")
        company_name = validated_data.pop("company_name")
        with transaction.atomic():
            last_receipt = Receipt.objects.filter(company__name=company_name).order_by("-print_number").first()
            print_number = 1
            if last_receipt is not None:
                now = timezone.now()
                date_created = last_receipt.date_created
                if not now.today().date() != date_created.date():
                    print_number = last_receipt.print_number + 1
            company = get_object_or_404(Company, name=company_name)
            receipt = Receipt.objects.create(
                **validated_data,
                company=company,
                print_number=print_number,
                receipt_number=print_number
            )
            for product in products:
                ReceiptProduct.objects.create(**product, receipt=receipt)
            receipt.refresh_from_db()
        return receipt

    def get_total_price(self, receipt):
        total_price = 0
        for product in receipt.products.all():
            total_price += product.get_full_price()
        return total_price

    def get_tax_values(self, receipt):
        vat_types = {"A": 0.23, "B": 0.08, "C": 0.05, "D": 0.00, "E": 1}
        tax_values = defaultdict(float)
        for product in receipt.products.all():
            if product.vat_type not in vat_types:
                continue
            tax_values[product.vat_type] += round(float(product.get_full_price()) * vat_types[product.vat_type], 2)
        return tax_values

    def get_total_tax(self, receipt):
        tax_values = self.get_tax_values(receipt)
        if "E" in tax_values:
            del tax_values["E"]
        return round(sum(tax_values.values()), 2)

    class Meta:
        model = Receipt
        fields = "__all__"


class InvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Invoice
        exclude = ("seller",)

    products = InvoiceProductSerializer(many=True)
    company = CompanySerializer(read_only=True)
    company_name = serializers.CharField(max_length=150, write_only=True)
    buyer_address = AddressSerializer()
    total_price = serializers.SerializerMethodField("get_total_price")

    def create(self, validated_data):
        products = validated_data.pop("products")
        company_name = validated_data.pop("company_name")
        buyer_address = validated_data.pop("buyer_address")
        with transaction.atomic():
            buyer_address = Address.objects.create(**buyer_address)
            company = get_object_or_404(Company, name=company_name)
            now = timezone.now()
            last_invoice = Invoice.objects.filter(seller=company).order_by("-date_created").first()
            invoice_count = 1
            if last_invoice is not None:
                year = last_invoice.date_created.year
                month = last_invoice.date_created.month
                if now.year == year and now.month == month:
                    last_invoice_count = int(last_invoice.invoice_number.split("/")[-1])
                    invoice_count = last_invoice_count + 1
            invoice_number = f"FV/{now.year}/{now.month}/{invoice_count}"
            invoice = Invoice.objects.create(
                **validated_data,
                invoice_number=invoice_number,
                seller=company,
                buyer_address=buyer_address
            )
            for product in products:
                InvoiceProduct.objects.create(**product, invoice=invoice)
            invoice.refresh_from_db()
        return invoice

    def validate_products(self, products):
        if not len(products):
            raise ValidationError("This field is required")
        return products

    def validate(self, data):
        nip = data.get('buyer_nip')
        pesel = data.get('buyer_pesel')
        if nip and not pesel:
            if not nip.isnumeric() or len(nip) != 10:
                raise ValidationError("Invalid NIP number")
            return data
        elif pesel and not nip:
            if not pesel.isnumeric() or len(pesel) != 11:
                raise ValidationError("Invalid PESEL number")
            return data
        else:
            raise ValidationError("Either nip or pesel must be included")

    def get_total_price(self, receipt):
        total_price = 0
        for product in receipt.products.all():
            total_price += product.get_full_price()
        return total_price
