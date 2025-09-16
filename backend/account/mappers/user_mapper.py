from account.models import UserModel
from account.domains.user_domain import UserDomain


def to_domain(user_model: UserModel) -> UserDomain: # model -> domain
    """Converts a UserModel instance to a UserDomain instance."""
    return UserDomain(
        id=user_model.id,
        username=user_model.username,
        email=user_model.email,
        first_name=user_model.first_name,
        last_name=user_model.last_name,
        phone=user_model.phone,
        role=user_model.role,
        created_on=user_model.created_on,
    )

def to_model(user_domain: UserDomain) -> UserModel:
    return UserModel.objects.get(id=user_domain.id)

# def to_model(user_domain: UserDomain) -> UserModel: # domain -> model
#     """Convert the UserDomain object to an existing UserModel object.
#     Returns:
#         UserModel. The UserModel representation of the UserDomain object.
#     Raises:
#         ValueError: If the user does not exist in the database.
#     """

#     if not user_domain.id:
#         raise ValueError("Cannot update an existing user without an id")

#     try:
#         user_model = UserModel.objects.get(id=user_domain.id)
#     except UserModel.DoesNotExist:
#         raise ValueError(f"User with id {user_domain.id} does not exist.")
        
#     # Update fields that are safe to overwrite
#     user_model.username = user_domain.username
#     user_model.email = user_domain.email
#     user_model.first_name = user_domain.first_name
#     user_model.last_name = user_domain.last_name
#     user_model.role = user_domain.role
#     user_model.phone = user_domain.phone
#     return user_model