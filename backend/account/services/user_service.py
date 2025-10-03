from typing import Optional, Any, Dict
from dataclasses import fields
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist

from account.domains.user_domain import UserDomain
from account.domains.register_domain import RegisterDomain
from account.domains.profile_domain import ProfileDomain
from account.domains.change_password_domain import ChangePasswordDomain
from account.domains.reset_password_domain import ResetPasswordDomain
from account.models import UserModel
from account.models import Profile
from account.services.exceptions import DomainError, UserNotFoundError, IncorrectPasswordError



# def register_user(domain: RegisterDomain) -> UserDomain:
#     """Register a new user and its profile (aggregate root = User)."""
#     domain.validate()

#     # enforce business invariants (uniqueness)
#     if UserModel.objects.filter(username=domain.username).exists():
#         raise DomainError("Username already taken")
#     if UserModel.objects.filter(email=domain.email).exists():
#         raise DomainError("Email already taken")

#     user_domain = UserDomain(username=domain.username,
#                              email=domain.email,
#                              raw_password=domain.password)

#     user = user_domain.to_model()
#     user.save()

#     # create profile aggregate part
#     profile_domain = ProfileDomain(user_id=user.id)
#     profile_domain.validate()
#     Profile.objects.create(**profile_domain.to_dict())

#     return UserDomain.from_model(user)


def register_user(data: dict) -> UserDomain:
    """Register a new user and its profile (aggregate root = User)."""

    # enforce business invariants (uniqueness)
    if UserModel.objects.filter(username=data['username']).exists():
        raise DomainError("Username already taken")
    if UserModel.objects.filter(email=data['email']).exists():
        raise DomainError("Email already taken")

    user_domain = UserDomain(username=data['username'],
                             email=data['email'],
                             raw_password=data['password'],
                             role=data['role'],
                             phone=data['phone'])

    user = user_domain.to_model()
    user.save()

    # create profile aggregate part
    user_domain.id = user.id
    profile_domain = user_domain.create_profile()
    profile_data = data.get('profile', {})
    Profile.objects.create(user=user, **profile_data)
    return UserDomain.from_model(user)


# def login_user(username_or_email: str, raw_password: str) -> UserDomain:
#     """Authenticate user by username/email + password."""
#     user = authenticate(username=username_or_email,
#                         password=raw_password)
#     if not user:
#         raise ValueError("Invalid credentials")
#     return UserDomain.from_model(user)


def change_password(user_id: int, old_password: str, new_password: str) -> bool:
    """Change password for a given user."""
    try:
        user = UserModel.objects.get(pk=user_id)
    except ObjectDoesNotExist:
        raise UserNotFoundError("User not found")

    if not user.check_password(old_password):
        raise IncorrectPasswordError("Old password is incorrect")

    user.set_password(new_password)
    user.save()
    return True


def reset_password(domain: ResetPasswordDomain) -> bool:
    """Reset password using reset token (stub)."""
    try:
        user = UserModel.objects.get(email=domain.email)
    except ObjectDoesNotExist:
        raise ValueError("User not found")

    # TODO: verify reset token properly
    if not domain.reset_token:
        raise ValueError("Invalid reset token")

    user.set_password(domain.new_password)
    user.save()
    return True


def get_user_by_id(user_id: int) -> UserDomain:
    user = UserModel.objects.get(pk=user_id)
    return UserDomain.from_model(user)


def get_user_by_username(username: str) -> UserDomain:
    user = UserModel.objects.get(username=username)
    return UserDomain.from_model(user)

def get_user_by_email(email: str) -> UserDomain:
    User = UserModel.objects.get(email=email)
    return UserDomain.from_model(User)


def update_user(user_id: int, updates: Dict[str, Any]) -> UserDomain:
    """Update user from domain object."""
    user = UserModel.objects.get(pk=user_id)
    domain = UserDomain.from_model(user)

    # Áp dụng updates và validate
    domain.apply_updates(updates)

    # Lưu vào database
    for key, value in updates.items():
        if hasattr(user, key):
            setattr(user, key, value)
    user.save()
    return domain


def deactivate_user(user_id: int) -> bool:
    try:
        user = UserModel.objects.get(id=user_id)
        user.is_active = False
        user.save()
        return True
    except UserModel.DoesNotExist:
        return False
    

def reactivate_user(user_id: int) -> Optional[UserDomain]:
    try:
        user = UserModel.objects.get(id=user_id)
        user.is_active = True
        user.save()
        return UserDomain.from_model(user)
    except UserModel.DoesNotExist:
        return None
    

def list_users(role: str = None, active_only: bool = True) -> list[UserDomain]:
    qs = UserModel.objects.all()
    if role:
        qs = qs.filter(role=role)
    if active_only:
        qs = qs.filter(is_active=True)
    return [UserDomain.from_model(u) for u in qs]

    
    

