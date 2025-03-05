from django.contrib import admin
from django.urls import path, include
from users.views import SignupView, LoginView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("admin/", admin.site.urls),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("api/", include("api.urls")),
]
