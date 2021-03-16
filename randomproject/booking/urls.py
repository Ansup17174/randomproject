from django.urls import path, include
from .views import ReceiptViewSet, CompanyViewSet, InvoiceViewSet
from rest_framework.routers import DefaultRouter

receipt_router = DefaultRouter()
receipt_router.register(prefix="receipt", viewset=ReceiptViewSet, basename="receipt")

company_router = DefaultRouter()
company_router.register(prefix="company", viewset=CompanyViewSet, basename="company")

invoice_router = DefaultRouter()
invoice_router.register(prefix="invoice", viewset=InvoiceViewSet, basename="invoice")


urlpatterns = [
    path("", include(receipt_router.urls)),
    path("", include(company_router.urls)),
    path("", include(invoice_router.urls))
]
