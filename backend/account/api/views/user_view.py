from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from account.models import UserModel, Profile, ParentalConsent
from account.domains.change_password_domain import ChangePasswordDomain
from account.api.permissions import IsAdminOrSelf
from account.serializers import (
    UserSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    ProfileSerializer,
    ParentalConsentSerializer,
)
from account.services import user_service, exceptions



# ---------- User detail & update ----------
class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/account/users/{id}/
    PATCH /api/account/users/{id}/  (owner or admin)
    """
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelf]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = user_service  # Khởi tạo service

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()

        # Validate input qua serializer
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            # Gọi service với validated data (dict)
            updated_domain = user_service.update_user(user_id=instance.id, updates=serializer.validated_data)

            # Serialize domain object thành response
            response_serializer = self.get_serializer(updated_domain)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except ValidationError as e:
            # Handle domain validation errors
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Handle unexpected errors
            return Response({"detail": "An error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        try:
            success = user_service.change_password(user_id=request.user.id, 
                                                   old_password=data["old_password"], 
                                                   new_password=data["new_password"])
        except exceptions.UserNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except exceptions.IncorrectPasswordError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": True}, status=status.HTTP_200_OK)