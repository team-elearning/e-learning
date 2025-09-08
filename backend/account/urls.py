from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView  # Optional: For token refresh endpoint
from .views import RegisterView, LoginView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),  # Optional: Token refresh endpoint
]
