from typing import Optional, Any, Dict, List
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction

from custom_account.domains.user_domain import UserDomain
from custom_account.domains.reset_password_domain import ResetPasswordDomain
from custom_account.models import UserModel
from custom_account.models import Profile
from core.exceptions import DomainError, UserNotFoundError, IncorrectPasswordError



def register_user(data: dict) -> UserDomain:
    """Register a new user and its profile (aggregate root = User)."""

    # enforce business invariants (uniqueness)
    if UserModel.objects.filter(username=data['username']).exists():
        raise DomainError("Username already taken")
    if UserModel.objects.filter(email=data['email']).exists():
        raise DomainError("Email already taken")
    
    phone = data.get('phone')
    if phone: 
        if UserModel.objects.filter(phone=phone).exists():
            raise DomainError("Số điện thoại đã tồn tại.")

    user_domain = UserDomain(username=data['username'],
                             email=data['email'],
                             raw_password=data['password'],
                             role=data['role'],
                             phone=data.get('phone'))

    user = user_domain.to_model()
    user.save()

    # create profile aggregate part
    user_domain.id = user.id
    profile_domain = user_domain.create_profile()
    profile_data = data.get('profile', {})
    Profile.objects.create(user=user, **profile_data)
    return UserDomain.from_model(user)


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


def admin_set_password(user_id: int, new_password: str):
    """
    Finds a user by ID and sets their password directly.
    Does not check the old password.
    Raises UserNotFoundError if the user doesn't exist.
    """
    try:
        user = UserModel.objects.get(id=user_id)
    except UserModel.DoesNotExist:
        raise UserNotFoundError("User not found.")
    
    # Use Django's set_password to handle hashing
    user.set_password(new_password)
    user.save(update_fields=["password"])


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
    
def delete_user(user_id):
    """
    Service-layer method to delete a user.
    Contains business logic for *if* a user can be deleted.
    """
    # Fetch the domain object from the repository
    user_to_delete = UserModel.objects.get(id=user_id)
    
    if not user_to_delete:
        raise ValidationError("User not found.")
    UserModel.delete(user_to_delete)
    

def list_all_users_for_admin() -> List[UserDomain]:
    """
    Gets all users as a list of UserDomain entities.

    This follows the style of 'register_user', where the service
    layer interacts with the Model but returns Domain Entities.
    """
    user_models = UserModel.objects.all().order_by('id')
    # [print(user.is_staff) for user in user_models]
    user_domains = [UserDomain.from_model(user) for user in user_models]
    return user_domains

@transaction.atomic
def synchronize_roles() -> dict:
    """
    Finds and fixes role/is_staff mismatches in the database.
    
    - If is_staff=True, role MUST be 'admin'.
    - If is_staff=False, role CANNOT be 'admin'.
    """
    
    # Fix users who ARE staff but their role IS NOT 'admin' (e.g., is_staff=True, role='student')
    updated_to_admin_count = UserModel.objects.filter(is_staff=True
                                             ).exclude(role='admin'
                                             ).update(role='admin')

    # Fix users who ARE NOT staff but their role IS 'admin' (e.g., is_staff=False, role='admin')
    updated_to_student_count = UserModel.objects.filter(is_staff=False,role='admin'
                                               ).update(role='student')

    # Return a report of what was fixed
    return {
        "users_updated_to_admin": updated_to_admin_count,
        "users_updated_from_admin": updated_to_student_count,
        "detail": "Role synchronization complete."
    }


    
    

