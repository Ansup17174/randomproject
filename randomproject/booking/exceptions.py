from rest_framework.views import exception_handler
from django.shortcuts import Http404


def custom_exception_handler(exception, context):
    response = exception_handler(exception, context)
    if response is not None and isinstance(exception, Http404):
        try:
            response.data['detail'] = exception.args[0]
        except IndexError:
            pass
    return response
