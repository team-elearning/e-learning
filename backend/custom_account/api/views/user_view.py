import logging
from django.http import Http404
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from custom_account.models import UserModel
from custom_account.domains.user_domain import UserDomain
from custom_account.api.dtos.user_dto import UpdateUserInput, UserPublicOutput, UserAdminOutput, UserInput
from custom_account.api.mixins import RoleBasedOutputMixin
from custom_account.serializers import UserSerializer, ChangePasswordSerializer, SetPasswordSerializer, RegisterSerializer
from custom_account.services import user_service, exceptions
from custom_account.services.exceptions import DomainError



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
class AdminUserListView(RoleBasedOutputMixin, APIView): 
    """
    GET /api/account/admin/users/    (admin) - List all users
    POST /api/account/admin/users/   (admin) - Create a new user
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    output_dto_public = UserPublicOutput
    output_dto_admin  = UserAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = user_service 

    def get(self, request):
        try:
            # Service returns a list of DOMAIN ENTITIES
            user_domains: list[UserDomain] = self.user_service.list_all_users_for_admin()
            
            return Response({"instance": user_domains}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to create a new user.
        """
        
        # Validate raw input format (using a DRF Serializer)
        serializer = RegisterSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create Input DTO from validated data
        try:
            # This DTO handles more specific validation (e.g., Pydantic)
            user_create_dto = UserInput(**validated_data)
        except Exception as e: # Catches Pydantic validation errors
            return Response({"detail": f"Invalid input data: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_user_domain: UserDomain = self.user_service.register_user(data=user_create_dto.to_dict())
            
            # Serialize DTO -> JSON 
            return Response(
                {"instance": new_user_domain}, 
                status=status.HTTP_201_CREATED
            )
        
        except DomainError as e: # Or your specific DomainError
            # Handle business logic errors (e.g., "Email already exists")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # Catch all other unexpected errors during service execution
            logger.error(f"Unexpected error in AdminUserListView (POST): {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred during user creation."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

logger = logging.getLogger(__name__)
class AdminUserDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /api/account/admin/users/{pk}/    (admin)
    PATCH /api/account/admin/users/{pk}/  (admin)
    DELETE /api/account/admin/users/{pk}/   (admin)
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    output_dto_public = UserPublicOutput
    output_dto_admin  = UserAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = user_service  

    def get_object(self, pk):
        """
        Helper method to get the user *model* from the DB.
        This is an infrastructure concern, which is fine for the View.
        """
        try:
            # Fetches the user specified by the URL's primary key (pk)
            return UserModel.objects.get(pk=pk)
        except UserModel.DoesNotExist:
            raise Http404

    def get(self, request, pk, *args, **kwargs):
        """
        Handles GET requests to retrieve a single user.
        """
        instance = self.get_object(pk)
        
        # The 'RoleBasedOutputMixin' will intercept raw model instance and 
        # convert it to the correct DTO (UserAdminOutput).
        return Response({"instance": instance})

    def patch(self, request, pk, *args, **kwargs):
        """
        Handles PATCH requests to update a single user.
        This follows the DDD "Command" flow.
        """
        instance = self.get_object(pk)

        # Validate input using the serializer
        serializer = UserSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        # Create Input DTO
        user_update_dto = UpdateUserInput(**validated_data)
        
        # Exclude 'None' values 
        updates_payload = user_update_dto.model_dump(exclude_unset=True)
        
        if not updates_payload:
            # Nothing to update, just return the current state
            return Response({"instance": instance}, status=status.HTTP_200_OK)

        try:
            updated_domain = self.user_service.update_user(
                user_id=instance.id, 
                updates=updates_payload
            )
            
            # Return the Domain Entity for the mixin to process
            return Response({"instance": updated_domain}, status=status.HTTP_200_OK)
        
        except ValidationError as e: # Or DomainError
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in AdminUserDetailView: {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, pk, *args, **kwargs):
        """
        Handles DELETE requests to remove a single user.
        """
        # Get the object. This will raise Http404 if not found.
        instance = self.get_object(pk)
        
        try:
            # Delegate the deletion logic to the application service
            self.user_service.delete_user(user_id=instance.id)
            
            return Response(status=status.HTTP_204_NO_CONTENT)

        except ValidationError as e: # Or a specific DomainError
            # e.g., "Cannot delete the last admin user"
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in AdminUserDetailView delete: {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AdminChangePasswordView(APIView):
    """
    Allows admin users to change any user's password.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id):
        """
        Handles the POST request to change a user's password.
        The user_id is taken from the URL.
        """
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            # Use a new service function designed for admins
            user_service.admin_set_password(
                user_id=user_id,
                new_password=data["new_password"]
            )
            
        except exceptions.UserNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Catch other potential errors
            return Response(
                {"detail": f"An unexpected error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"detail": "Password changed successfully."}, 
            status=status.HTTP_200_OK
        )


class AdminMaintenanceView(APIView):
    """
    POST /api/account/admin/users/sync-roles/  (admin)
    
    A utility endpoint to find and fix data mismatches
    between the 'is_staff' flag and the 'role' field.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_sync_service = user_service.synchronize_roles

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to trigger the synchronization.
        """
        try:
            report = self.role_sync_service()
            return Response(report, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error during role synchronization: {e}", exc_info=True)
            return Response(
                {"detail": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    