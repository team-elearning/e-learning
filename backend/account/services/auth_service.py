from django.contrib.auth.tokens import PasswordResetTokenGenerator

from account.models import UserModel
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
    reset_link = f"https://frontend-app/reset-password?email={user.email}&token={token}"
    
    email_service = get_email_service()
    email_service.send(
        to=email,
        subject="Password Reset Request",
        body=f"Click the link to reset your password: {reset_link}"
    )


def reset_password_confirm(email: str, token: str, new_password: str) -> bool:
    try:
        user = UserModel.objects.get(email=email)
    except UserModel.DoesNotExist:
        return False

    # TODO: verify token properly
    if token != "RANDOM-TOKEN":
        return False

    user.set_password(new_password)
    user.save()
    return True