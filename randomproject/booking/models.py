from django.db import models
from uuid import uuid4
from django.core.validators import MinValueValidator


class Address(models.Model):
    street = models.CharField(max_length=32)
    building_number = models.CharField(max_length=10)
    post_code = models.CharField(max_length=6)
    city = models.CharField(max_length=36)
    country = models.CharField(max_length=42)


class Product(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=100, decimal_places=2, validators=[MinValueValidator(0)])
    vat_letter = models.CharField(max_length=1)
    on_dicsount = models.BooleanField(default=False)
    discount_value = models.DecimalField(max_digits=100, decimal_places=2, validators=[MinValueValidator(0)])


class Receipt(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    header = models.CharField(max_length=50, null=True, blank=True)
    company_name = models.CharField(max_length=150)
    company_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="receipts")
    sales_point = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="receipts")
    nip_number = models.IntegerField(max_length=10)
    print_number = models.PositiveIntegerField()
    date_printed = models.DateTimeField()
    currency = models.CharField(max_length=10)
    number = models.PositiveIntegerField()
    checkout_number = models.CharField(max_length=50)
    buyer_nip = models.IntegerField(max_length=10, null=True, blank=True)

