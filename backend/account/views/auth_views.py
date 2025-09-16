from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from account.mappers import user_mapper
from account.services import user_service
from account.serializers import UserSerializer, RegisterSerializer, LoginSerializer



class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_domain = user_service.create_new_user(**serializer.validated_data)
            return Response(UserSerializer(user_domain.to_dict()).data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data) # Call LoginSerializer
        serializer.is_valid(raise_exception=True)

        login_domain = serializer.to_main()
        user_domain = user_service.authenticate_user(login_domain)

        if not user_domain:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # convert domain -> model for JWT
        try:
            user_model = user_mapper.to_model(user_domain)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        # Generate tokens    
        refresh = RefreshToken.for_user(user_model)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user_domain.to_dict()).data
        }, status=status.HTTP_200_OK)
    