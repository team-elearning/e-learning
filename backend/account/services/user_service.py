from backend.account.domains.user_domain import UserDomain
from backend.account.models import UserModel
from typing import Optional
from django.contrib.auth.hashers import check_password, make_password

def to_domain(user_model: UserModel) -> UserDomain:
    """Converts a UserModel instance to a UserDomain instance."""
    return UserDomain(
        id=user_model.id,
        username=user_model.username,
        email=user_model.email,
        first_name=user_model.first_name,
        last_name=user_model.last_name,
        phone=user_model.phone,
        role=user_model.role,
        is_active=user_model.is_active,
        created_on=user_model.created_on,
    )


# Create
def create_new_user(username: str, email: str, raw_password: str, role="student", **extra) -> UserDomain:
    """Creates a new user and commits it to the DB."""
    if UserModel.objects.filter(username=username).exists():
        raise ValueError(f"Username {username} already exists.")
    if UserModel.objects.filter(email=email).exists():
        raise ValueError(f"Email {email} already exists.")
    
    # Create domain first → validate business rules
    user_domain = UserDomain(
        username=username,
        email=email,
        password=raw_password,
        role=role,
        first_name=extra.get('first_name'),
        last_name=extra.get('last_name'),
        phone=extra.get('phone')
    )

    user_model = UserModel.objects.create(
        username=username,
        email=email,
        role=role,
        password=make_password(raw_password),
        first_name=extra.get('first_name'),
        last_name=extra.get('last_name'),
        phone=extra.get('phone'),
    )
    return user_model.to_domain()


# Authenticate
def authenticate_user(username_or_email: str, raw_password: str) -> Optional[UserDomain]:
    """Authenticates a user by username/email and password."""
    try:
        user = UserModel.objects.get(username=username_or_email)
    except UserModel.DoesNotExist:
        try:
            user = UserModel.objects.get(email=username_or_email)
        except UserModel.DoesNotExist:
            return None
    
    if not check_password(raw_password, user.password):
        return None
    return user.to_domain()


# Get
def get_user_domain(*, user_id: int = None, username: str = None, email: str = None) -> Optional[UserDomain]:
    """Fetches a user by ID, username, or email."""
    try:
        if user_id is not None:
            user = UserModel.objects.get(id=user_id)
        elif username is not None:
            user = UserModel.objects.get(username=username)
        elif email is not None:
            user = UserModel.objects.get(email=email)
        else:
            return None
        return user.to_domain()
    except UserModel.DoesNotExist:
        return None


# def get_user_domain_for_token(*, user_id: int = None, username: str = None) -> Optional[UserModel]:
#     """Fetches the UserModel instance for JWT token generation."""
#     try:
#         if user_id is not None:
#             return UserModel.objects.get(id=user_id).to_domain()
#         elif username is not None:
#             return UserModel.objects.get(username=username).to_domain()
#         return None
#     except UserModel.DoesNotExist:
#         return None


# Update
def update_user(user_id: int, **updates) -> Optional[UserDomain]:
    """Update user attributes and return updated domain object."""
    try:
        user_model = UserModel.objects.get(id=user_id)

        if "username" in updates:
            if UserModel.objects.filter(username=updates["username"]).exclude(id=user_id).exists():
                raise ValueError(f"Username {updates['username']} already exists.")
        if "email" in updates:
            if UserModel.objects.filter(email=updates["email"]).exclude(id=user_id).exists():
                raise ValueError(f"Email {updates['email']} already exists.")
        if "password" in updates:
            temp_domain = user_model.to_domain()
            temp_domain.change_password(updates["password"])
            user_model.password = make_password(updates["password"])
            del updates["password"]  # Remove to avoid setting it again below

        for key, value in updates.items():
            if key == 'password':
                value = make_password(value)
            if hasattr(user_model, key):
                setattr(user_model, key, value)
        user_model.save()
        return user_model.to_domain()
    except UserModel.DoesNotExist:
        return None
    

