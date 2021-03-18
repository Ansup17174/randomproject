from django_filters import rest_framework as filters
from .models import Receipt, Invoice


class ReceiptFilter(filters.FilterSet):

    min_print_number = filters.NumberFilter(field_name="print_number", lookup_expr="gte")
    max_print_number = filters.NumberFilter(field_name="print_number", lookup_expr="lte")

    min_checkout_number = filters.NumberFilter(field_name="checkout_number", lookup_expr="gte")
    max_checkout_number = filters.NumberFilter(field_name="checkout_number", lookup_expr="lte")

    min_receipt_number = filters.NumberFilter(field_name="receipt_number", lookup_expr="gte")
    max_receipt_number = filters.NumberFilter(field_name="receipt_number", lookup_expr="lte")

    class Meta:
        model = Receipt
        fields = ["header", "print_number", "currency", "receipt_number", "checkout_number", "buyer_nip"]


class InvoiceFilter(filters.FilterSet):

    date_created_range = filters.DateFromToRangeFilter(field_name="date_created")
    date_finished_range = filters.DateFromToRangeFilter(field_name="date_finished")

    class Meta:
        model = Invoice
        fields = ["date_created", "date_finished", "is_prepayment"]
