from rest_framework import serializers
from .models import Product, Address, Receipt


class ProductSerializer(serializers.ModelSerializer):

    def get_total_price(self, product):
        return product.quantity * product.unit_price

    def get_total_discount_price(self, product):
        return product.quantity * (product.unit_price - product.discount_value)

    total_price = serializers.SerializerMethodField("get_total_price")

    class Meta:
        model = Product
        fields = "__all__"


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = "__all__"


class ReceiptSerializer(serializers.ModelSerializer):

    products = ProductSerializer(many=True)

    class Meta:
        model = Receipt
