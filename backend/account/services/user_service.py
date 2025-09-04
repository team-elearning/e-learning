from backend.account.domains.user_domain import UserDomain
from backend.account.models import UserModel
from typing import Optional
from django.contrib.auth.hashers import check_password, make_password

def to_domain(user: UserModel) -> UserDomain:
    """Converts a UserModel instance to a UserDomain instance."""
    return UserDomain(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        created_on=user.created_on,
    )


def create_new_user(username: str, email: str, raw_password: str, role="student", **extra) -> UserDomain:
    """Creates a new user and commits it to the DB."""
    if UserModel.objects.filter(username=username).exists():
        raise ValueError(f"Username {username} already exists.")
    if UserModel.objects.filter(email=email).exists():
        raise ValueError(f"Email {email} already exists.")
    
    user = UserModel.objects.create(
        username=username,
        email=email,
        role=role,
        password=make_password(raw_password),
        first_name=extra.get('first_name'),
        last_name=extra.get('last_name'),
        phone=extra.get('phone'),
    )
    return user.to_domain()


def get_user_by_username(username: str) -> Optional[UserDomain]:
    """Fetches a user by username."""
    try:
        user = UserModel.objects.get(username=username)
        return user.to_domain()
    except UserModel.DoesNotExist:
        return None
    

def get_user_by_email(email: str) -> Optional[UserDomain]:
    """Fetches a user by email."""
    try:
        user = UserModel.objects.get(email=email)
        return user.to_domain()
    except UserModel.DoesNotExist:
        return None
    

def get_user_by_id(user_id: int) -> Optional[UserDomain]:
    """Fetches a user by ID."""
    try:
        user = UserModel.objects.get(id=user_id)
        return user.to_domain()
    except UserModel.DoesNotExist:
        return None
    

def authenticate_user(username_or_email: str, raw_password: str) -> Optional[UserDomain]:
    """Authenticates a user by username/email and password."""
    try:
        user = UserModel.objects.get(username=username_or_email)
    except UserModel.DoesNotExist:
        try:
            user = UserModel.objects.get(email=username_or_email)
        except UserModel.DoesNotExist:
            return None
    
    if check_password(raw_password, user.password):
        return user.to_domain()
    return None


def update_user(user_id: int, **updates) -> Optional[UserDomain]:
    """Update user attributes and return updated domain object."""
    try:
        user = UserModel.objects.get(id=user_id)
        for key, value in updates.items():
            if key == 'password':
                value = make_password(value)
            if hasattr(user, key):
                setattr(user, key, value)
        user.save()
        return user.to_domain()
    except UserModel.DoesNotExist:
        return None