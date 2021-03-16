from django.db import models
from django.contrib.auth.models import AbstractUser
from uuid import uuid4


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    date_of_birth = models.DateField(null=True)
    phone = models.CharField(max_length=9, null=True)
