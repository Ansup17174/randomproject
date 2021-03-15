from django.urls import path, include
from .views import ReceiptViewSet, CompanyViewSet
from rest_framework.routers import DefaultRouter

receipt_router = DefaultRouter()
receipt_router.register(prefix="receipt", viewset=ReceiptViewSet, basename="receipt")

company_router = DefaultRouter()
company_router.register(prefix="company", viewset=CompanyViewSet, basename="company")


urlpatterns = [
    path("auth/registration/", include('dj_rest_auth.registration.urls')),
    path("auth/", include('dj_rest_auth.urls')),
    path("", include(receipt_router.urls)),
    path("", include(company_router.urls))
]
