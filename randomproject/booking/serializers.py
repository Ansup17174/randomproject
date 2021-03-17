from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import ReceiptProduct, Address, Receipt, Company, InvoiceProduct, Invoice, InvoicePrepayment
from collections import defaultdict
from django.utils import timezone


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        exclude = ("id",)


class CompanySerializer(serializers.ModelSerializer):

    company_address = AddressSerializer()

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

    class Meta:
        model = Company
        exclude = ("owner", "id")


class ReceiptProductSerializer(serializers.ModelSerializer):

    price = serializers.SerializerMethodField("get_price")
    total_discount_value = serializers.SerializerMethodField("get_total_discount_value")
    full_price = serializers.SerializerMethodField("get_full_price")

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

    class Meta:
        model = ReceiptProduct
        exclude = ("id", "receipt")


class ReceiptSerializer(serializers.ModelSerializer):

    company = CompanySerializer(read_only=True)
    company_name = serializers.CharField(max_length=150, write_only=True)
    sales_point = AddressSerializer(required=False)
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
        sales_point = validated_data.pop("sales_point")
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
            if sales_point is not None:
                sales_point_address = Address.objects.create(**sales_point)
                receipt.sales_point = sales_point_address
                receipt.save()
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
            if product.vat_type == "E":
                continue
            full_price = product.get_full_price()
            tax_value = round(float(full_price) - float(full_price) / (vat_types[product.vat_type]+1), 2)
            tax_values[product.vat_type] += tax_value
        return tax_values

    def get_total_tax(self, receipt):
        tax_values = self.get_tax_values(receipt)
        if "E" in tax_values:
            del tax_values["E"]
        return round(sum(tax_values.values()), 2)

    class Meta:
        model = Receipt
        exclude = ("id",)


class InvoiceProductSerializer(serializers.ModelSerializer):

    net_price = serializers.SerializerMethodField("get_net_price")
    tax_value = serializers.SerializerMethodField("get_vat_tax")
    gross_price = serializers.SerializerMethodField("get_gross_price")

    def get_net_price(self, product):
        return product.get_net_price()

    def get_vat_tax(self, product):
        return product.get_vat_tax()

    def get_gross_price(self, product):
        return product.get_gross_price()

    class Meta:
        model = InvoiceProduct
        exclude = ("invoice", "id")


class InvoicePrepaymentSerializer(serializers.ModelSerializer):

    gross_price = serializers.SerializerMethodField("get_gross_price")

    def get_gross_price(self, invoice_prepayment):
        return invoice_prepayment.get_gross_price()

    class Meta:
        model = InvoicePrepayment
        exclude = ("id", "invoice")


class InvoiceSerializer(serializers.ModelSerializer):

    products = InvoiceProductSerializer(many=True)
    company = CompanySerializer(read_only=True)
    invoice_prepayment = InvoicePrepaymentSerializer(required=False)
    company_name = serializers.CharField(max_length=150, write_only=True)
    buyer_address = AddressSerializer()
    tax_data = serializers.SerializerMethodField("get_tax_data")
    total_gross_price = serializers.SerializerMethodField("get_total_gross_price")

    def create(self, validated_data):
        user = self.context.get('request').user
        products = validated_data.pop("products")
        company_name = validated_data.pop("company_name")
        buyer_address = validated_data.pop("buyer_address")
        invoice_prepayment = validated_data.pop("invoice_prepayment")
        with transaction.atomic():
            buyer_address = Address.objects.create(**buyer_address)
            company = get_object_or_404(Company, name=company_name, owner=user)
            now = timezone.now()
            last_invoice = Invoice.objects.filter(company=company).order_by("-date_created").first()
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
                company=company,
                buyer_address=buyer_address
            )
            for product in products:
                InvoiceProduct.objects.create(**product, invoice=invoice)
            if invoice_prepayment is not None:
                InvoicePrepayment.objects.create(**invoice_prepayment, invoice=invoice)
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
            raise ValidationError("Either NIP or PESEL must be included")

    def get_tax_data(self, invoice):
        tax_data = {
            "total_net_price": 0,
            "total_tax_value": 0
        }
        for product in invoice.products.all():
            total_net_price = product.get_net_price()
            tax_value = product.get_vat_tax()
            total_gross_price = product.get_gross_price()
            vat_key = float(product.vat_tax)
            tax_data['total_net_price'] += total_net_price
            tax_data['total_tax_value'] += tax_value
            if vat_key not in tax_data:
                tax_data[vat_key] = {
                    "total_net_price": total_net_price,
                    "tax_value": tax_value,
                    "total_gross_price": total_gross_price
                }
            else:
                vat_type = tax_data[vat_key]
                vat_type['total_net_price'] += total_net_price
                vat_type['tax_value'] += tax_value
                vat_type['total_gross_price'] += total_gross_price
        return tax_data

    def get_total_gross_price(self, invoice):
        total_price = 0
        for product in invoice.products.all():
            total_price += product.get_gross_price()
        return total_price

    class Meta:
        model = Invoice
        exclude = ("id",)
