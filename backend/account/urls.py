from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView  # For token refresh endpoint

from account.api.views.auth_view import RegisterView, LogoutView, ResetPasswordRequestView, ResetPasswordConfirmView, CustomTokenObtainPairView, AdminLoginAsUserView, AdminRefreshUserAccessView, AdminLogoutUserView
from account.api.views.user_view import AdminUserListView, CurrentUserDetailView, ChangePasswordView
from account.api.views.profile_view import UserProfileView, AdminProfileView, AdminProfileListView
from account.api.views.parental_consent_view import ParentalConsentListView, ParentalConsentCreateView, ParentalConsentRevokeView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="account-register"),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("user/", CurrentUserDetailView.as_view(), name="current-user"),
    path("password/change/", ChangePasswordView.as_view(), name="account-change-password"),
    path("password/reset/", ResetPasswordRequestView.as_view(), name="account-reset-request"),
    path("password/reset/confirm/", ResetPasswordConfirmView.as_view(), name="account-reset-confirm"),
    path("profile/", UserProfileView.as_view(), name="account-profile"),

    path("users/", AdminUserListView.as_view(), name="account-user-list"),
    path("users/<int:user_id>/", AdminUserListView.as_view(), name="account-user-detail"),

    path("profiles/", AdminProfileListView.as_view(), name="account-profile"),
    path("profiles/<int:user_id>/", AdminProfileView.as_view(), name="account-profile"),

    path("consents/", ParentalConsentListView.as_view(), name="account-consents-list"),
    path("consents/grant/", ParentalConsentCreateView.as_view(), name="account-consents-grant"),
    path("consents/revoke/", ParentalConsentRevokeView.as_view(), name="account-consents-revoke"),


    path("admin/login/<int:user_id>/", AdminLoginAsUserView.as_view(), name="admin-login-as-user"),
    path('admin/refresh-access/<int:user_id>/', AdminRefreshUserAccessView.as_view(), name='admin_refresh_access'),
    path('admin/logout-user/<int:user_id>/', AdminLogoutUserView.as_view(), name='admin_logout_user'),
]
