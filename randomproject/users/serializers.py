from datetime import datetime

from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

UserModel = get_user_model()


class CustomRegisterSerializer(RegisterSerializer):

    first_name = serializers.CharField()
    last_name = serializers.CharField()
    date_of_birth = serializers.DateField()
    phone = serializers.CharField(max_length=9)

    def validate_date_of_birth(self, date_of_birth):
        if not datetime(1900, 1, 1).date() < date_of_birth < datetime.now().date():
            raise ValidationError("Invalid date of birth")
        return date_of_birth

    def validate_phone(self, phone):
        if not phone.isnumeric():
            raise ValidationError("Invalid phone number")
        return phone

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'first_name': self.validated_data.get('first_name'),
            'last_name': self.validated_data.get('last_name'),
            'email': self.validated_data.get('email', ''),
            'phone': self.validated_data.get('phone'),
            'date_of_birth': self.validated_data.get('date_of_birth')
        }


class CustomUserDetailsSerializer(UserDetailsSerializer):

    class Meta:
        extra_fields = []
        # see https://github.com/jazzband/dj-rest-auth/issues/181
        # UserModel.XYZ causing attribute error while importing other
        # classes from `serializers.py`. So, we need to check whether the auth model has
        # the attribute or not
        if hasattr(UserModel, "USERNAME_FIELD"):
            extra_fields.append(UserModel.USERNAME_FIELD)
        if hasattr(UserModel, "EMAIL_FIELD"):
            extra_fields.append(UserModel.EMAIL_FIELD)

        model = UserModel
        fields = ('pk', *extra_fields, 'first_name', 'last_name', 'phone', 'date_of_birth')
        read_only_fields = ('email',)
