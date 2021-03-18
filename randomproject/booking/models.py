from django.db import models
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator


class Address(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
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
    nip_number = models.CharField(max_length=10)


class Receipt(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    header = models.CharField(max_length=50, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    sales_point = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="receipts"
    )
    print_number = models.PositiveIntegerField(editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    currency = models.CharField(max_length=10)
    receipt_number = models.PositiveIntegerField(editable=False)
    checkout_number = models.CharField(max_length=50, null=True, blank=True)
    buyer_nip = models.CharField(max_length=10, null=True, blank=True)


class ReceiptProduct(models.Model):
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


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    buyer_name = models.CharField(max_length=100)
    buyer_address = models.ForeignKey(Address, on_delete=models.PROTECT)
    buyer_nip = models.CharField(max_length=10, null=True, blank=True)
    buyer_pesel = models.CharField(max_length=11, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_finished = models.DateField()
    invoice_number = models.CharField(max_length=20, editable=False)
    currency = models.CharField(max_length=10)
    is_prepayment = models.BooleanField(default=False)
    previous_prepayment = models.CharField(max_length=30, null=True, blank=True)


class InvoiceProduct(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=15)
    quantity = models.DecimalField(max_digits=20, decimal_places=3, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    discount_value = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        default=0
    )
    vat_tax = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def get_net_price(self):
        return round(self.quantity * self.unit_price, 2)

    def get_vat_tax(self):
        return round(float(self.get_net_price()) * float(self.vat_tax) / 100, 2)

    def get_gross_price(self):
        return float(self.get_net_price()) + self.get_vat_tax()


class InvoicePrepayment(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="prepayments")
    net_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    vat_tax = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def get_tax_value(self):
        return round(float(self.net_price) * (float(self.vat_tax) / 100), 2)

    def get_gross_price(self):
        return round(float(self.net_price) + self.get_tax_value(), 2)
