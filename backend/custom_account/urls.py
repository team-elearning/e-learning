from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView  # For token refresh endpoint
from dj_rest_auth.views import LoginView, LogoutView, PasswordResetView

from custom_account.api.views.auth_view import RegisterView, AdminLoginAsUserView, AdminRefreshUserAccessView, AdminLogoutUserView, AdvancedPasswordResetConfirmView
from custom_account.api.views.user_view import AdminUserListView, CurrentUserDetailView, ChangePasswordView, AdminUserDetailView, AdminChangePasswordView, AdminMaintenanceView
from custom_account.api.views.profile_view import UserProfileView, AdminProfileListView, AdminProfileDetailView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="account-register"),
    path('login/', LoginView.as_view(), name='account_login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("user/", CurrentUserDetailView.as_view(), name="current-user"),
    path("profile/", UserProfileView.as_view(), name="account-profile"),
    path("password/change/", ChangePasswordView.as_view(), name="account-change-password"),
    path('password/reset/', PasswordResetView.as_view(), name='password_reset_request'),
    re_path(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$', AdvancedPasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path("admin/login/<uuid:user_id>/", AdminLoginAsUserView.as_view(), name="admin-login-as-user"),
    path('admin/refresh-access/<uuid:user_id>/', AdminRefreshUserAccessView.as_view(), name='admin_refresh_access'),
    path('admin/logout-user/<uuid:user_id>/', AdminLogoutUserView.as_view(), name='admin_logout_user'),
    path("admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path('admin/maintenance/', AdminMaintenanceView.as_view(), name='admin-system-maintenance'),
    path("admin/users/<uuid:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/profiles/", AdminProfileListView.as_view(), name="admin-profile-list"),
    path("admin/profiles/<uuid:user_id>/", AdminProfileDetailView.as_view(), name="admin-profile"),
    path("admin/password/set/<uuid:user_id>/", AdminChangePasswordView.as_view(), name="admin-set-password"),
]
