# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework import status
# from rest_framework.response import Response

# from account.services import user_service
# from account.serializers import UserSerializer
# from account.api.permissions import IsAdminOrSelf

# class UserProfileView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminOrSelf]

#     # Get user profile
#     def get(self, request):
#         # Determine target user
#         target_user_id = request.query_params.get('user_id', request.user.id)
        
#         user_domain = user_service.get_user_domain(user_id=target_user_id)

#         if not user_domain:
#             return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
#         # Check object-level permission
#         self.check_object_permissions(request, user_domain)

#         return Response(UserSerializer(user_domain.to_dict()).data, status=status.HTTP_200_OK)


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
        # ensure profile exists or return 404
        profile = get_object_or_404(Profile, user=self.request.user)
        return profile

    def perform_update(self, serializer):
        # call service for updating profile (so domain validations run)
        profile_domain = serializer.validated_data
        # For simplicity delegate to user_service
        user_service.update_profile(user_id=self.request.user.id, data=serializer.validated_data)
        # return updated profile done by generic view
    

