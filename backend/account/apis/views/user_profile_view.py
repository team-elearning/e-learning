from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from account.services import user_service
from account.api.serializers import UserSerializer
from account.api.permissions import IsAdminOrSelf

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSelf]

    # Get user profile
    def get(self, request):
        # Determine target user
        target_user_id = request.query_params.get('user_id', request.user.id)
        
        user_domain = user_service.get_user_domain(user_id=target_user_id)

        if not user_domain:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check object-level permission
        self.check_object_permissions(request, user_domain)

        return Response(UserSerializer(user_domain.to_dict()).data, status=status.HTTP_200_OK)
    

