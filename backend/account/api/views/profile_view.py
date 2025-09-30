from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from account.models import UserModel, Profile, ParentalConsent
from account.api.permissions import IsAdminOrSelf
from account.serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    ProfileSerializer,
    ParentalConsentSerializer,
)
from account.services import user_service, auth_service, profile_service



# ---------- Profile endpoints ----------
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/account/profile/  -> get current user's profile
    PATCH /api/account/profile/ -> update current user's profile
    Admins can GET other profiles via /api/account/profiles/{user_id}/ (you can add an admin view)
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user_id = self.request.query_params.get("user_id")

        if user_id:
            # Nếu có query param user_id → chỉ admin mới được xem
            if not self.request.user.is_staff:
                raise PermissionDenied("You do not have permission to view this profile.")

            target_user = get_object_or_404(UserModel, pk=user_id)
            return get_object_or_404(Profile, user=target_user)

        # Nếu không có user_id → luôn trả về profile của chính mình
        return get_object_or_404(Profile, user=self.request.user)


    def perform_update(self, serializer):
        profile_domain = serializer.to_domain()
        profile_service.update_profile(user_id=self.request.user.id, data=profile_domain.to_dict())


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    

