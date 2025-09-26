from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView  # For token refresh endpoint

from backend.account.api.views.auth_view import RegisterView, LoginView, LogoutView, ResetPasswordRequestView, ResetPasswordConfirmView
from backend.account.api.views.user_view import UserListView, UserDetailView, ChangePasswordView
from backend.account.api.views.profile_view import ProfileView
from backend.account.api.views.parental_consent_view import ParentalConsentListView, ParentalConsentCreateView, ParentalConsentRevokeView

urlpatterns = [
    # path("register/", RegisterView.as_view(), name="register"),
    # path("login/", LoginView.as_view(), name="login"),
    # path("profile/", UserProfileView.as_view(), name="user-profile"),
    # path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    # path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),

    # path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    # path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),  # Token refresh endpoint

    path("register/", RegisterView.as_view(), name="account-register"),
    path("login/", LoginView.as_view(), name="account-login"),
    path("logout/", LogoutView.as_view(), name="account-logout"),

    path("users/", UserListView.as_view(), name="account-user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="account-user-detail"),

    path("password/change/", ChangePasswordView.as_view(), name="account-change-password"),
    path("password/reset/", ResetPasswordRequestView.as_view(), name="account-reset-request"),
    path("password/reset/confirm/", ResetPasswordConfirmView.as_view(), name="account-reset-confirm"),

    path("profile/", ProfileView.as_view(), name="account-profile"),
    path("consents/", ParentalConsentListView.as_view(), name="account-consents-list"),
    path("consents/grant/", ParentalConsentCreateView.as_view(), name="account-consents-grant"),
    path("consents/revoke/", ParentalConsentRevokeView.as_view(), name="account-consents-revoke"),
]
