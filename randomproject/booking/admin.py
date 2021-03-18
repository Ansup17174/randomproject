from django.contrib import admin
from .models import Receipt, Address, ReceiptProduct, InvoiceProduct, Invoice, Company, InvoicePrepayment


admin.site.register(Receipt)
admin.site.register(Address)
admin.site.register(ReceiptProduct)
admin.site.register(Invoice)
admin.site.register(InvoiceProduct)
admin.site.register(Company)
admin.site.register(InvoicePrepayment)
