from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView  # For token refresh endpoint

from account.views.auth_views import RegisterView, LoginView
from account.views.password_views import ForgotPasswordView, ResetPasswordView
from account.views.user_profile_view import UserProfileView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),

    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),  # Token refresh endpoint
]
