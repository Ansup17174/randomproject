from django.db import models
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUser(AbstractUser):
    date_of_birth = models.DateField()
    phone = models.CharField(max_length=9)


class Address(models.Model):
    street = models.CharField(max_length=32)
    building_number = models.CharField(max_length=10)
    post_code = models.CharField(max_length=6)
    city = models.CharField(max_length=36)
    country = models.CharField(max_length=42)


User = get_user_model()


class Company(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="companies")
    name = models.CharField(max_length=150, unique=True)
    company_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="companies")
    nip_number = models.PositiveIntegerField(validators=[MaxValueValidator(9999999999)])


class Receipt(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    header = models.CharField(max_length=50, null=True, blank=True)
    company_name = models.CharField(max_length=150)
    company_address = models.ForeignKey(Address, on_delete=models.PROTECT)
    sales_point = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="receipts"
    )
    nip_number = models.CharField(max_length=10)
    print_number = models.PositiveIntegerField()
    date_printed = models.DateTimeField()
    currency = models.CharField(max_length=10)
    receipt_number = models.PositiveIntegerField()
    checkout_number = models.CharField(max_length=50, null=True, blank=True)
    buyer_nip = models.CharField(max_length=10, null=True, blank=True)


class Product(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(max_digits=100, decimal_places=2, validators=[MinValueValidator(0)])
    vat_type = models.CharField(max_length=1)
    discount_value = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name="products")

    def get_full_price(self):
        return round(self.quantity * (self.unit_price - self.discount_value), 2)

