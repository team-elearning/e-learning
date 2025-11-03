import logging
from django.http import Http404
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from account.models import UserModel, Profile
from account.domains.profile_domain import ProfileDomain
from account.api.mixins import RoleBasedOutputMixin
from account.api.dtos.profile_dto import ProfilePublicOutput, ProfileAdminOutput, ProfileUpdateInput
from account.serializers import ProfileSerializer
from account.services import profile_service



# ---------- Profile endpoints ----------
class UserProfileView(RoleBasedOutputMixin, APIView):
    """
    GET /api/account/profile/  -> get current user's profile
    PATCH /api/account/profile/ -> update current user's profile
    """
    permission_classes = [permissions.IsAuthenticated]

    output_dto_public = ProfilePublicOutput
    output_dto_admin = ProfileAdminOutput

    def get(self, request):
        """
        Handle GET requests to retrieve the user's profile.
        """
        profile_domain = profile_service.get_profile_by_user(user_id=request.user.id)
        
        # Put the domain object in the response for the mixin to serialize
        return Response({"instance": profile_domain}, status=status.HTTP_200_OK)

    def patch(self, request):
        """
        Handle PATCH requests to update the user's profile.
        """
        # Use a dedicated serializer *only* for validation
        serializer = ProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create an Input DTO from validated data
        profile_input_dto = ProfileUpdateInput(**serializer.validated_data)

        # Call the service with the DTO's data
        updated_profile_domain = profile_service.update_profile(
            user_id=request.user.id, 
            data=profile_input_dto.to_dict()
        )

        # Return the updated domain object for the mixin to serialize
        return Response({"instance": updated_profile_domain}, status=status.HTTP_200_OK)
    

# ---- Admin ----
class AdminProfileListView(APIView):
    """
    GET /api/account/admin/profiles/ -> list all profiles (admin only)
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile_service = profile_service 

    def get(self, request):
        try:
            # Service returns a list of DOMAIN ENTITIES
            profile_domains: list[ProfileDomain] = self.profile_service.list_all_profiles()
            
            # 2. Converts Domain -> DTO (using Pydantic)
            output_dtos = [
                ProfileAdminOutput.model_validate(domain) for domain in profile_domains
            ]
            
            # Serialize the list of DTOs into JSON
            json_data = [dto.model_dump() for dto in output_dtos]
            
            # Return the JSON list
            return Response(json_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

logger = logging.getLogger(__name__)
class AdminProfileDetailView(RoleBasedOutputMixin, APIView):
    """
    POST   /api/account/profiles/{user_id}/ -> Create a default profile for this user (admin only)
    GET    /api/account/profiles/{user_id}/ -> Retrieve any user's profile (admin only)
    PATCH  /api/account/profiles/{user_id}/ -> Partially update any user's profile (admin only)
    DELETE /api/account/profiles/{user_id}/ -> Delete any user's profile (admin only)
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    output_dto_public = ProfilePublicOutput
    output_dto_admin = ProfileAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile_service = profile_service  

    def get_object(self, user_id):
        """
        Helper method to get the *profile model* from the DB
        based on the user_id in the URL.
        """
        try:
            user = UserModel.objects.get(pk=user_id)
            return Profile.objects.get(user=user)
        except (UserModel.DoesNotExist, Profile.DoesNotExist):
            raise Http404

    def post(self, request, user_id, *args, **kwargs):
        """
        Handles POST requests to create a default profile for the user.
        This follows the DDD "Command" flow and takes no input body.
        """
        try:
            # Delegate to application service
            # The user_id comes directly from the URL
            created_domain = self.profile_service.create_default_profile(user_id=user_id)
            
            # Return the new Domain Entity for the mixin to process
            return Response(
                {"instance": created_domain}, 
                status=status.HTTP_201_CREATED
            )
        
        except ValidationError as e: # Or a specific DomainError
            # e.g., "User not found" or "Profile already exists"
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in AdminProfileDetailView POST: {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, user_id, *args, **kwargs):
        """
        Handles GET requests to retrieve a single user's profile.
        """
        instance = self.get_object(user_id)
        
        # The 'RoleBasedOutputMixin' will intercept the raw model 
        # and convert it to the correct DTO (ProfileAdminOutput).
        return Response({"instance": instance})

    def patch(self, request, user_id, *args, **kwargs):
        """
        Handles PATCH requests to update a single user's profile.
        This follows the DDD "Command" flow.
        """
        instance = self.get_object(user_id)

        # Validate input using the serializer
        serializer = ProfileSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        # Create Input DTO
        profile_update_dto = ProfileUpdateInput(**validated_data)
        
        # Exclude 'None' values (or unset)
        updates_payload = profile_update_dto.model_dump(exclude_unset=True)
        
        if not updates_payload:
            # Nothing to update, just return the current state
            return Response({"instance": instance}, status=status.HTTP_200_OK)

        try:
            # Delegate to application service
            updated_domain = self.profile_service.update_profile(
                user_id=instance.user_id, 
                updates=updates_payload
            )
            
            # Return the Domain Entity for the mixin to process
            return Response({"instance": updated_domain}, status=status.HTTP_200_OK)
        
        except ValidationError as e: # Or a specific DomainError
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in AdminProfileDetailView: {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, user_id, *args, **kwargs):
        """
        Handles DELETE requests to remove a single user's profile.
        """
        # Get the object. This will raise Http404 if not found.
        instance = self.get_object(user_id)
        
        try:
            # Delegate the deletion logic to the application service
            self.profile_service.delete_profile(user_id=instance.user_id)
            
            return Response(status=status.HTTP_204_NO_CONTENT)

        except ValidationError as e: # Or a specific DomainError
            # e.g., "Cannot delete profile with active subscription"
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in AdminProfileDetailView delete: {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    

