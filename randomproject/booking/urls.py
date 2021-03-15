from django.urls import path, include
from .views import ReceiptViewSet
from rest_framework.routers import DefaultRouter
receipt_router = DefaultRouter()
receipt_router.register(prefix="receipt", viewset=ReceiptViewSet, basename="receipt")


urlpatterns = [
    path("", include(receipt_router.urls))
]
