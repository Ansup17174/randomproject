from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from dj_rest_auth.views import LoginView, UserDetailsView
from dj_rest_auth.registration.views import RegisterView

public_patterns = [
    path("api/", include("booking.urls")),
    path("auth/registration/", RegisterView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/user", UserDetailsView.as_view())
]

schema_view = get_schema_view(
    openapi.Info(
        title="Booking app",
        default_version="v1",
        description="Application for handling invoices and receipts",
    ),
    public=True,
    permission_classes=(AllowAny,),
    patterns=public_patterns
)


urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path('admin/', admin.site.urls),
    path("api/", include("booking.urls")),
    path("auth/", include("users.urls")),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc')
]
