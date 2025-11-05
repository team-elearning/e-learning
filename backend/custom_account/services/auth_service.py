from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError

from custom_account.models import UserModel
from infrastructure.email_service import get_email_service



token_generator = PasswordResetTokenGenerator()

# password reset flow
def reset_password_request(email: str) -> None:
    """
    Generate a reset token and trigger email sending.
    """
    try:
        user = UserModel.objects.get(email=email)
    except UserModel.DoesNotExist:
        raise ValueError("User not found")

    token = token_generator.make_token(user)
    # reset_link = f"{settings.FRONTEND_URL}/account/password/reset/confirm/?email={user.email}&token={token}"
    reset_link = f"http://127.0.0.1:8000/api/account/password/reset/confirm/?email={user.email}&token={token}"
  
    try: 
        email_service = get_email_service()
        email_service.send(
            to=email,
            subject="Password Reset Request",
            body=f"Click the link to reset your password: {reset_link}"
        )
        return True
    except Exception as e:
        return False


def reset_password_confirm(email: str, token: str, new_password: str) -> bool:
    try:
        user = UserModel.objects.get(email=email)
    except UserModel.DoesNotExist:
        return False

    # Verify token properly
    if not default_token_generator.check_token(user, token):
        return False

    user.set_password(new_password)
    user.save()
    return True


def authenticate_user(username_or_email: str, password: str) -> UserModel:
    """
    Authenticate a user by username or email and password.
    Raises ValidationError if authentication fails.
    Returns the authenticated User object.
    """
    user = UserModel.objects.filter(username=username_or_email).first() or \
            UserModel.objects.filter(email=username_or_email).first()
    if user is None or not user.check_password(password) or not user.is_active:
        raise ValidationError("No active account found with the given credentials")
    return user