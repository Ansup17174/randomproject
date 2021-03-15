from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Product, Address, Receipt, Company
from collections import defaultdict


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = "__all__"

    def create(self, validated_data):
        user = self.context['request'].user
        company = Company.objects.create(**validated_data, owner=user)
        return company


class ProductSerializer(serializers.ModelSerializer):

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
        model = Product
        exclude = ("receipt",)


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = "__all__"


class ReceiptSerializer(serializers.ModelSerializer):

    def validate_products(self, products):
        if not len(products):
            raise ValidationError("This field is required.")
        return products

    def create(self, validated_data):
        products = validated_data.pop("products")
        company_address = validated_data.pop("company_address")
        with transaction.atomic():
            address = Address.objects.create(**company_address)
            receipt = Receipt.objects.create(**validated_data, company_address=address)
            for product in products:
                Product.objects.create(**product, receipt=receipt)
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

    total_price = serializers.SerializerMethodField("get_total_price")
    tax_values = serializers.SerializerMethodField("get_tax_values")
    total_tax = serializers.SerializerMethodField("get_total_tax")
    products = ProductSerializer(many=True)
    company_address = AddressSerializer()

    class Meta:
        model = Receipt
        fields = "__all__"
