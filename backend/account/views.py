from django.shortcuts import render
from rest_framework.views import APIView
from .models import UserModel
from rest_framework import status
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from .services import user_services


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Service returns a UserDomain object
                user_domain = user_services.create_new_user(**serializer.validated_data)

                # Convert domain -> dict -> serializer
                user_dict = user_domain.to_dict()
                return Response(UserSerializer(user_dict).data, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user_domain = user_services.authenticate_user(
                serializer.validated_data['username_or_email'], 
                serializer.validated_data['password']
            )

            if not user_domain:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Return domain object as dict
            user_dict = user_domain.to_dict()

            # Generate JWT token
            user_model = user_services.get_user(user_domain.id).to_existing_model()
            if not user_model:
                return Response({"error": "User not found for token generation"}, status=status.HTTP_404_NOT_FOUND)
            
            refresh = RefreshToken.for_user(user_model)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user_dict).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

