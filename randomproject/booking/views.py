from rest_framework.viewsets import ModelViewSet
from .serializers import ReceiptSerializer, CompanySerializer
from .models import Receipt, Company


class ReceiptViewSet(ModelViewSet):

    serializer_class = ReceiptSerializer
    queryset = Receipt.objects.all()


class CompanyViewSet(ModelViewSet):

    serializer_class = CompanySerializer
    queryset = Company.objects.all()


# TODO company viewset authentication
