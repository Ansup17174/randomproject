from django.contrib import admin
from .models import Receipt, Address, ReceiptProduct


admin.register(Receipt)
admin.register(Address)
admin.register(ReceiptProduct)
