from django_filters import rest_framework as filters
from .models import Receipt, Invoice


class ReceiptFilter(filters.FilterSet):

    date_created = filters.IsoDateTimeFromToRangeFilter()

    class Meta:
        model = Receipt
        fields = {
            "header": ["icontains", "exact"],
            "print_number": ["lte", "gte", "exact"],
            "currency": ["exact"],
            "receipt_number": ["lte", "gte", "exact"],
            "checkout_number": ["lte", "gte", "exact"],
            "buyer_nip": ["exact"]
        }


class InvoiceFilter(filters.FilterSet):

    date_created = filters.IsoDateTimeFromToRangeFilter()
    date_finished = filters.DateFromToRangeFilter()

    class Meta:
        model = Invoice
        fields = ["date_created", "date_finished", "is_prepayment"]
