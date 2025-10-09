from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.views import TokenObtainPairView

from account.models import UserModel, Profile, ParentalConsent
from account.domains.register_domain import RegisterDomain
from account.api.permissions import IsAdminOrSelf
from account.serializers import (
    UserSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    ProfileSerializer,
    ParentalConsentSerializer,
)
from account.services import user_service, auth_service
from account.serializers import CustomTokenObtainPairSerializer



class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # call service with domain object
        user_domain = user_service.register_user(data=data)

        # map domain -> response dict (use UserSerializer.from_domain or usual serializer)
        return Response(UserSerializer.from_domain(user_domain), status=status.HTTP_201_CREATED)
    

# ---------- Login (token-based) ----------
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# class LoginView(APIView):
#     permission_classes = [permissions.AllowAny]

#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         data = serializer.validated_data
#         identifier = data["username_or_email"]
#         raw_password = data["raw_password"]

#         # authenticate by username or email (robust)
#         user = None
#         try:
#             user = UserModel.objects.get(username=identifier)
#         except UserModel.DoesNotExist:
#             try:
#                 user = UserModel.objects.get(email=identifier)
#             except UserModel.DoesNotExist:
#                 user = None

#         if not user or not user.check_password(raw_password):
#             return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

#         # create or return token (DRF TokenAuth)
#         token, _ = Token.objects.get_or_create(user=user)

#         # return token + user data (use domain mapping)
#         user_domain = user_service.get_user_by_id(user.id)
#         return Response({
#             "token": token.key,
#             "user": UserSerializer.from_domain(user_domain),
#         })
    

# ---------- Logout ----------
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Get the refresh token from the request body
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()  # Add the refresh token to the blacklist
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (InvalidToken, TokenError) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    

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

        try:
            # call auth service: it will generate token and call email adapter
            success = auth_service.reset_password_request(email=email)

            if success:
                return Response({"detail": "Password reset email sent successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Email not found or failed to send"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": f"Error sending email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # # don't reveal whether email exists (security): respond 204
        # return Response(status=status.HTTP_204_NO_CONTENT)


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



    