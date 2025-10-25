from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView  # For token refresh endpoint

from account.api.views.auth_view import RegisterView, LogoutView, ResetPasswordRequestView, ResetPasswordConfirmView, CustomTokenObtainPairView
from account.api.views.user_view import UserListView, UserDetailView, ChangePasswordView
from account.api.views.profile_view import ProfileView
from account.api.views.parental_consent_view import ParentalConsentListView, ParentalConsentCreateView, ParentalConsentRevokeView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="account-register"),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),

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
