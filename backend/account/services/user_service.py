from typing import Optional
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist

from account.domains.user_domain import UserDomain, LoginDomain
from account.domains.register_domain import RegisterDomain
from account.domains.change_password_domain import ChangePasswordDomain
from account.domains.reset_password_domain import ResetPasswordDomain
from account.models import UserModel



# # Create
# def create_new_user(username: str, email: str, password: str, role="student", **extra) -> UserDomain:
#     """Creates a new user and commits it to the DB."""
#     if UserModel.objects.filter(username=username).exists():
#         raise ValueError(f"Username {username} already exists.")
#     if UserModel.objects.filter(email=email).exists():
#         raise ValueError(f"Email {email} already exists.")
    
#     # Create domain first → validate business rules
#     user_domain = UserDomain(
#         username=username,
#         email=email,
#         role=role,
#         first_name=extra.get('first_name'),
#         last_name=extra.get('last_name'),
#         phone=extra.get('phone')
#     )
#     user_domain.validate()

#     # Save to DB
#     user_model = UserModel.objects.create(
#         username=username,
#         email=email,
#         role=role,
#         password=make_password(password),
#         first_name=extra.get('first_name'),
#         last_name=extra.get('last_name'),
#         phone=extra.get('phone'),
#     )

#     return UserDomain.from_model(user_model)


# # Authenticate - check and return if user exists
# def authenticate_user(login_domain: LoginDomain) -> Optional[UserDomain]:
#     """Authenticates a user by username/email and password."""
#     username_or_email = login_domain.username_or_email
#     raw_password = login_domain.raw_password

#     user_model = authenticate(username=username_or_email,
#                               password=raw_password)

#     if not user_model:
#         return None
#     return UserDomain.from_model(user_model)


# # Get
# def get_user_domain(*, user_id: int = None, username: str = None, email: str = None) -> Optional[UserDomain]:
#     """Fetches a user by ID, username, or email."""
#     try:
#         if user_id is not None:
#             user_model = UserModel.objects.get(id=user_id)
#         elif username is not None:
#             user_model = UserModel.objects.get(username=username)
#         elif email is not None:
#             user_model = UserModel.objects.get(email=email)
#         else:
#             return None
#         return UserDomain.from_model(user_model)
#     except UserModel.DoesNotExist:
#         return None


# # Update
# def update_user(user_id: int = None, user_domain: UserDomain = None, **updates) -> Optional[UserDomain]:
#     """Update user attributes and return updated domain object."""
#     try:
#         if user_domain:
#             user_id = user_domain.id
#             updates = {
#                 "username": user_domain.username,
#                 "email": user_domain.email,
#                 "role": user_domain.role,
#                 "is_staff": user_domain.is_staff,
#             }

#         user_model = UserModel.objects.get(id=user_id)

#         if "username" in updates:
#             if UserModel.objects.filter(username=updates["username"]).exclude(id=user_id).exists():
#                 raise ValueError(f"Username {updates['username']} already exists.")
#         if "email" in updates:
#             if UserModel.objects.filter(email=updates["email"]).exclude(id=user_id).exists():
#                 raise ValueError(f"Email {updates['email']} already exists.")
#         if "password" in updates:
#             temp_domain = user_model.to_domain()
#             temp_domain.change_password(updates["password"])
#             user_model.password = make_password(updates["password"])
#             del updates["password"]  # Remove to avoid setting it again below

#         for key, value in updates.items():
#             if key == 'password':
#                 value = make_password(value)
#             if hasattr(user_model, key):
#                 setattr(user_model, key, value)
#         user_model.save()
#         return UserDomain.from_model(user_model)
    
#     except UserModel.DoesNotExist:
#         return None
    

# # login 
# def login_user(username_or_email: str, password: str) -> Optional[UserDomain]:
#     """High-level login use case"""
#     return authenticate_user(username_or_email, password)



def register_user(domain: RegisterDomain) -> UserDomain:
    """Register a new user."""
    domain.validate()
    user = UserModel.objects.create_user(
        username=domain.username,
        email=domain.email,
        password=domain.password,
        role=domain.role,
        phone=domain.phone,
    )
    return UserDomain.from_model(user)


def login_user(domain: LoginDomain) -> UserDomain:
    """Authenticate user by username/email + password."""
    user = authenticate(username=domain.username_or_email,
                        password=domain.raw_password)
    if not user:
        raise ValueError("Invalid credentials")
    return UserDomain.from_model(user)


def change_password(domain: ChangePasswordDomain) -> bool:
    """Change password for a given user."""
    try:
        user = UserModel.objects.get(pk=domain.user_id)
    except ObjectDoesNotExist:
        raise ValueError("User not found")

    if not user.check_password(domain.old_password):
        raise ValueError("Old password is incorrect")

    user.set_password(domain.new_password)
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


def update_user(user_id: int, data: dict) -> UserDomain:
    """Update user fields."""
    user = UserModel.objects.get(pk=user_id)
    for field, value in data.items():
        setattr(user, field, value)
    user.save()
    return UserDomain.from_model(user)


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

    
    

