from rest_framework.viewsets import ModelViewSet
from .serializers import ReceiptSerializer
from .models import Receipt


class ReceiptViewSet(ModelViewSet):

    serializer_class = ReceiptSerializer
    queryset = Receipt.objects.all()
