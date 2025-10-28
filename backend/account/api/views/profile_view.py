from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from account.models import UserModel, Profile
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
class AdminProfileListView(generics.ListAPIView):
    """
    GET /api/account/profiles/ -> list all profiles (admin only)
    """
    queryset = Profile.objects.select_related("user").all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminProfileView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/account/profiles/{user_id}/ -> Retrieve any user's profile (admin only)
    PUT    /api/account/profiles/{user_id}/ -> Update any user's profile (admin only)
    PATCH  /api/account/profiles/{user_id}/ -> Partially update any user's profile (admin only)
    DELETE /api/account/profiles/{user_id}/ -> Delete any user's profile (admin only)
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_object(self):
        user_id = self.kwargs["user_id"]
        target_user = get_object_or_404(UserModel, pk=user_id)
        return get_object_or_404(Profile, user=target_user)

    

