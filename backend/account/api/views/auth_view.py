from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from account.api.dtos.user_dto import UserInput, UserPublicOutput, UserAdminOutput
from account.api.mixins import RoleBasedOutputMixin
from account.serializers import (RegisterSerializer, ResetPasswordSerializer)
from account.services import user_service, auth_service
from account.services.exceptions import DomainError
from account.serializers import CustomTokenObtainPairSerializer



class RegisterView(RoleBasedOutputMixin, APIView):
    permission_classes = [permissions.AllowAny]

    output_dto_public = UserPublicOutput
    output_dto_admin = UserAdminOutput

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_input_dto = UserInput(**serializer.validated_data)

        try:
            # call service with domain object
            user_domain = user_service.register_user(data=user_input_dto.to_dict()) # Pass the domain object

        except DomainError as e: # <-- Catch DomainError
            # Catch the custom domain error from your service
            return Response(
                {"error": str(e)}, # Use the error message from the exception
                status=status.HTTP_400_BAD_REQUEST
            )

        except IntegrityError:
            # Catch the database error when a unique constraint fails
            return Response(
                {"error": "A user with that username or email already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Put the domain object in the response so the mixin can pick it up
        return Response({"instance": user_domain}, status=status.HTTP_201_CREATED)
    

# ---------- Login (token-based) ----------
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

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
    



User = get_user_model()
# --- Admin (only)
class AdminLoginAsUserView(APIView):
    """
    An admin-only view to obtain JWT tokens for any user.
    The admin must be authenticated and be a superuser/staff.
    
    Usage: POST /api/login/admin-as/<user_id>/
    """
    # This is crucial: only allow authenticated admin users
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request, user_id, *args, **kwargs):
        """
        Takes a user_id from the URL and returns access/refresh tokens
        for that user.
        """
        # Find the user we want to log in as
        # get_object_or_404 will automatically return a 404 response if user not found
        try:
            user_to_login = get_object_or_404(User, pk=user_id)
        except Exception:
             return Response(
                {"error": f"User with ID {user_id} not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Generate tokens for the specified user
        refresh = RefreshToken.for_user(user_to_login)
             
        try:
            # Validate the Django user model against the Pydantic DTO
            user_data_dto = UserAdminOutput.model_validate(user_to_login)
            # Use your existing method to get the dictionary
            user_data_dict = user_data_dto.to_dict(exclude_none=True)
        except Exception as e:
            # Catch errors if your User model doesn't match the DTO
            return Response(
                {"error": f"Failed to serialize user data: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        response_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data_dict  # <-- Use the dictionary from the DTO
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    

class AdminRefreshUserAccessView(APIView):
    """
    An admin-only view to obtain a new *access token* for any user.
    This does NOT generate a new refresh token.
    
    Usage: POST /api/admin/refresh-access/<user_id>/
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request, user_id, *args, **kwargs):
        """
        Takes a user_id from the URL and returns a new access token
        for that user, along with the user's data.
        """
        try:
            user_to_refresh = get_object_or_404(User, pk=user_id)
        except Exception:
            return Response(
                {"error": f"User with ID {user_id} not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Generate an access token
        access = AccessToken.for_user(user_to_refresh)
        
        # Serialize user data using Pydantic DTO
        try:
            # Validate the Django user model against the Pydantic DTO
            user_data_dto = UserAdminOutput.model_validate(user_to_refresh)
            # Use method to get the dictionary
            user_data_dict = user_data_dto.to_dict(exclude_none=True)
        except Exception as e:
            # Catch errors if your User model doesn't match the DTO
            return Response(
                {"error": f"Failed to serialize user data: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # 3. Format the response as requested
        response_data = {
            'access': str(access),
            'user': user_data_dict  # <-- Use the dictionary from the DTO
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    

class AdminLogoutUserView(APIView):
    """
    An admin-only view to force-logout any user by blacklisting
    all of their outstanding refresh tokens.
    
    Usage: POST /api/admin/logout-user/<user_id>/
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request, user_id, *args, **kwargs):
        """
        Takes a user_id from the URL and blacklists all of their
        refresh tokens.
        """
        try:
            user_to_logout = get_object_or_404(User, pk=user_id)
        except Exception:
            return Response(
                {"error": f"User with ID {user_id} not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Find all outstanding refresh tokens for the user
        # OutstandingToken only stores refresh tokens
        tokens = OutstandingToken.objects.filter(user=user_to_logout)
        
        # Blacklist each token
        count = 0
        for token in tokens:
            # get_or_create ensures we don't add duplicate entries
            _, created = BlacklistedToken.objects.get_or_create(token=token)
            if created:
                count += 1
        
        return Response(
            {"detail": f"Successfully logged out user {user_to_logout.username}. Blacklisted {count} refresh token(s)."},
            status=status.HTTP_200_OK
        )



    