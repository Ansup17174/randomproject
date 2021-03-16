from rest_framework.viewsets import ModelViewSet
from .serializers import ReceiptSerializer, CompanySerializer
from .models import Receipt, Company


class ReceiptViewSet(ModelViewSet):

    serializer_class = ReceiptSerializer

    def get_queryset(self):
        return Receipt.objects.filter(company__owner=self.request.user)


class CompanyViewSet(ModelViewSet):

    serializer_class = CompanySerializer

    def get_queryset(self):
        return Company.objects.filter(owner=self.request.user)
