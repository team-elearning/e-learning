from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from account.models import UserModel, Profile, ParentalConsent
from account.api.permissions import IsOwnerOrAdmin
from account.serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    ProfileSerializer,
    ParentalConsentSerializer,
)
from account.services import user_service, auth_service



# ---------- User detail & update ----------
class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/account/users/{id}/
    PATCH /api/account/users/{id}/  (owner or admin)
    """
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def update(self, request, *args, **kwargs):
        # validate via serializer then call service update_user to ensure business rules applied in service/domain
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updates = serializer.validated_data

        # call service layer
        updated_domain = user_service.update_user(user_id=instance.id, user_domain=None, **updates)
        return Response(UserSerializer.from_domain(updated_domain))


# ---------- List users (admin) ----------
class UserListView(generics.ListAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    # add filtering/pagination as needed


# ---------- Change password (user logged in) ----------
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # call service
        success = user_service.change_password(
            user_id=request.user.id,
            old_password=data["old_password"],
            new_password=data["new_password"],
        )
        if not success:
            return Response({"detail": "Old password incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True}, status=status.HTTP_200_OK)