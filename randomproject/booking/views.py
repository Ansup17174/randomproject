from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import ReceiptSerializer, CompanySerializer, InvoiceSerializer
from .models import Receipt, Company, Invoice


class CompanyViewSet(ModelViewSet):

    serializer_class = CompanySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]

    def get_queryset(self):
        return Company.objects.filter(owner=self.request.user)


class InvoiceViewSet(ModelViewSet):

    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["buyer_name", "buyer_nip", "buyer_pesel", "invoice_number", "currency", "previous_prepayment"]
    filterset_fields = ["date_created", "date_finished", "is_prepayment"],
    ordering_fields = ["buyer_name", "buyer_nip", "buyer_pesel", "date_created", "date_finished"
                       "invoice_number", "currency", "is_prepayment"]

    def get_queryset(self):
        return Invoice.objects.filter(company__owner=self.request.user)


class ReceiptViewSet(ModelViewSet):

    serializer_class = ReceiptSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["header", "print_number", "currency", "receipt_number", "checkout_number", "buyer_nip"]
    search_fields = ["header"]
    ordering_fields = ["print_number", "receipt_number", "date_created", "currency"]

    def get_queryset(self):
        return Receipt.objects.filter(company__owner=self.request.user)
