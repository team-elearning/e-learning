from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from account.models import UserModel
from account.api.permissions import IsAdmin
from account.api.dtos.user_dto import UpdateUserInput, UserPublicOutput, UserAdminOutput
from account.api.mixins import RoleBasedOutputMixin
from account.serializers import UserSerializer, ChangePasswordSerializer
from account.services import user_service, exceptions



# ---------- User detail & update ----------
class CurrentUserDetailView(RoleBasedOutputMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    output_dto_public = UserPublicOutput
    output_dto_admin  = UserAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = user_service

    def get(self, request):
        return Response({"instance": request.user})

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # Create the DTO from ALL validated data
        update_dto = UpdateUserInput(**validated_data)

        # Create the update payload, but exclude any 'None' values.
        updates_payload = update_dto.model_dump(exclude_none=True)

        # If the payload is empty after stripping Nones, just return.
        if not updates_payload:
            return Response({"instance": request.user}, status=200)

        try:
            updated = self.user_service.update_user(
                user_id=request.user.id,
                updates=updates_payload,
            )
            return Response({"instance": updated}, status=200)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)
        


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
    


# ---------- List users (admin) ----------
class AdminUserDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /api/account/users/{id}/    (by owner or admin)
    PATCH /api/account/users/{id}/  (by owner or admin)
    """
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    output_dto_public = UserPublicOutput
    output_dto_admin  = UserAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = user_service  # Khởi tạo service

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        return Response({"instance": self.get_object()})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Validate input qua serializer
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        if not request.user.is_staff:
            allowed_fields = {"username", "email", "phone"}
            validated_data = {k: v for k, v in validated_data.items() if k in allowed_fields}
        user_update_dto = UpdateUserInput(**validated_data)

        try:
            # Gọi service với validated data (dict)
            updated_domain = user_service.update_user(user_id=instance.id, updates=user_update_dto.to_dict())
            return Response({"instance": updated_domain}, status=status.HTTP_200_OK)
            # # Serialize domain object thành response
            # response_serializer = self.get_serializer(updated_domain)
            # user_output_dto = UserOutput(**response_serializer.data)
            # return Response(user_output_dto.to_dict(), status=status.HTTP_200_OK)
        
        except ValidationError as e:
            # Handle domain validation errors
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Handle unexpected errors
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AdminUserListView(generics.ListAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    # add filtering/pagination as needed