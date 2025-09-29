# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework_simplejwt.tokens import RefreshToken

# from account.api.serializers import UserSerializer, RegisterSerializer, LoginSerializer
# from account.services import user_service
# from account.models import UserModel



# class RegisterView(APIView):
#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         try:
#             user_domain = user_service.create_new_user(**serializer.validated_data)
#             return Response(UserSerializer(user_domain.to_dict()).data, status=status.HTTP_201_CREATED)
            
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# class LoginView(APIView):
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data) # Call LoginSerializer
#         serializer.is_valid(raise_exception=True)

#         login_domain = serializer.to_domain()
#         user_domain = user_service.authenticate_user(login_domain)

#         if not user_domain:
#             return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

#         # convert domain -> model for JWT
#         try:
#             user_model = UserModel.objects.get(id=user_domain.id)
#         except ValueError as e:
#             return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
#         # Generate tokens    
#         refresh = RefreshToken.for_user(user_model)

#         return Response({
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#             'user': UserSerializer(user_domain.to_dict()).data
#         }, status=status.HTTP_200_OK)



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



class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # call your service function (function-based)
        user_domain = user_service.register_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],  # assume serializer uses 'password'
            role=data.get("role", "student"),
            phone=data.get("phone"),
        )

        # map domain -> response dict (use UserSerializer.from_domain or usual serializer)
        return Response(UserSerializer.from_domain(user_domain), status=status.HTTP_201_CREATED)
    

# ---------- Login (token-based) ----------
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        identifier = data["username_or_email"]
        raw_password = data["raw_password"]

        # authenticate by username or email (robust)
        user = None
        try:
            user = UserModel.objects.get(username=identifier)
        except UserModel.DoesNotExist:
            try:
                user = UserModel.objects.get(email=identifier)
            except UserModel.DoesNotExist:
                user = None

        if not user or not user.check_password(raw_password):
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # create or return token (DRF TokenAuth)
        token, _ = Token.objects.get_or_create(user=user)

        # return token + user data (use domain mapping)
        user_domain = user_service.get_user_domain(user_id=user.id)
        return Response({
            "token": token.key,
            "user": UserSerializer.from_domain(user_domain),
        })
    

# ---------- Logout ----------
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # if using TokenAuth: simply delete the token
        if hasattr(request.auth, "delete"):
            request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

# ---------- Reset password request (send email) ----------
class ResetPasswordRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        # For request we only need email; ResetPasswordSerializer can accept email only for request step
        # but for simplicity we accept serializer (it may validate other fields too)
        serializer.is_valid(raise_exception=False)
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # call auth service: it will generate token and call email adapter
        auth_service.reset_password_request(email=email)
        # don't reveal whether email exists (security): respond 204
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Reset password confirm ----------
class ResetPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # expected: {email, token, new_password}
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        ok = auth_service.reset_password_confirm(
            email=data["email"],
            token=data["reset_token"],
            new_password=data["new_password"]
        )
        if not ok:
            return Response({"detail": "Invalid token or request"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True}, status=status.HTTP_200_OK)



    