from django.shortcuts import render
from rest_framework.decorators import api_view
from .models import AppUser
from rest_framework import status
from .serializers import AppUserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response

# Create your views here.

# Register View
@api_view(['POST'])
def register(request):
    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    username = request.data.get('username')
    role = request.data.get('role', 'student')  # Default role is 'student
    phone = request.data.get('phone')

    if AppUser.objects.filter(email=email).exists():
        return Response("Email already registered", status = status.HTTP_400_BAD_REQUEST)
    
    user = AppUser(email=email, first_name=first_name, last_name=last_name, username=username, role=role, phone=phone)
    user.set_password(password)
    user.save()

    return Response(AppUserSerializer(user).data, status = status.HTTP_201_CREATED)

# Login View
@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    try:
        user = AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return Response("Invalid email or password", status = status.HTTP_400_BAD_REQUEST)
    
    if not user.check_password(password):
        return Response("Invalid email or password", status = status.HTTP_400_BAD_REQUEST)
    
    # Create JWT token
    refresh = RefreshToken.for_user(user)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': AppUserSerializer(user).data
    }, status = status.HTTP_200_OK)
