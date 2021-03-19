from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import NotAcceptable
from django.http import StreamingHttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import ReceiptSerializer, CompanySerializer, InvoiceSerializer
from .models import Receipt, Company, Invoice
from .filters import ReceiptFilter, InvoiceFilter
import csv


class CompanyViewSet(ModelViewSet):

    serializer_class = CompanySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]

    def get_queryset(self):
        return Company.objects.filter(owner=self.request.user)


class InvoiceViewSet(ModelViewSet):

    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = InvoiceFilter
    ordering_fields = ["buyer_name", "buyer_nip", "buyer_pesel", "date_created", "date_finished"
                       "invoice_number", "currency", "is_prepayment"]

    def get_queryset(self):
        return Invoice.objects.filter(company__owner=self.request.user)


class ReceiptViewSet(ModelViewSet):

    serializer_class = ReceiptSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ReceiptFilter
    search_fields = ["header"]
    ordering_fields = ["print_number", "receipt_number", "date_created", "currency"]

    def get_queryset(self):
        return Receipt.objects.filter(company__owner=self.request.user)


class PseudoBuffer:

    def write(self, value):
        return value


class SalesReportView(APIView):

    def get(self, request, doctype):
        if doctype not in ("invoice", "receipt"):
            raise NotAcceptable("Type must be invoice or receipt")
        buffer = PseudoBuffer()
        writer = csv.writer(buffer)
        if doctype == "invoice":
            fields = ["Seller", "Buyer", "Marketplace", "Country", "InvoiceId",
                      "TransactionTime", "MarketplaceCurrency", "NetPrice", "TotalTax", "GrossPrice"]
            invoices = list(Invoice.objects.filter(company__owner=request.user).values_list(
                "company__name",
                "buyer_name",
                "company__website",
                "company__company_address__country",
                "id",
                "date_finished",
                "currency",
                "net_price",
                "total_tax",
                "gross_price"
            ))
            invoices.insert(0, fields)
            rows = (writer.writerow(row) for row in invoices)
            response = StreamingHttpResponse(rows, content_type="text/csv")
            response['Content-Disposition'] = 'attachment; filename=report.csv'
            return response

        elif doctype == "receipt":
            fields = ["Seller", "ReceiptId", "Country", "TransactionTime",
                      "MarketplaceCurrency", "TotalTax", "GrossPrice"]
            receipts = list(Receipt.objects.filter(company__owner=request.user).values_list(
                "company__name",
                "id",
                "company__company_address__country",
                "date_created",
                "currency",
                "total_tax",
                "gross_price"
            ))
            receipts.insert(0, fields)
            rows = (writer.writerow(row) for row in receipts)
            response = StreamingHttpResponse(rows, content_type="text/csv")
            response['Content-Disposition'] = "attachment; filename=report.csv"
            return response


