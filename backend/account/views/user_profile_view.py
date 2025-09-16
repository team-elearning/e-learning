from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from account.services import user_service
from rest_framework import status
from rest_framework.response import Response
from account.serializers import UserSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    # Get user profile
    def get(self, request):
        # Current logged-in user
        current_user_id = request.user.id
        current_user = user_service.service.get_user_domain(user_id=current_user_id)
        if not current_user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Admins can view other users' profiles  
        target_user_id = request.query_params.get("user_id")
        if target_user_id:
            if current_user.role != "admin":
                return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            user_domain = user_service.service.get_user_domain(user_id=target_user_id)
            if not user_domain:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Students see only their own profile
            user_domain = current_user

        return Response(UserSerializer(user_domain.to_dict()).data, status=status.HTTP_200_OK)
    

