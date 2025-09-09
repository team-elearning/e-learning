from account.models import UserModel

# domain to model
def to_new_model(self) -> UserModel:
    """Convert the UserDomain object to a UserModel object.
    Returns:
        UserModel. The UserModel representation of the UserDomain object.
    """
    return UserModel(
        username=self.username,
        password=self.password,
        email=self.email,
        first_name=self.first_name,
        last_name=self.last_name,
        role=self.role,
        phone=self.phone
    )
    
def to_existing_model(self) -> UserModel:
    """Convert the UserDomain object to an existing UserModel object.
    Returns:
        UserModel. The UserModel representation of the UserDomain object.
    Raises:
        ValueError: If the user does not exist in the database.
    """

    if not self.id:
        raise ValueError("Cannot update an existing user without an id")

    try:
        user_model = UserModel.objects.get(id=self.id)
    except UserModel.DoesNotExist:
        raise ValueError(f"User with id {self.id} does not exist.")
        
    # Update fields that are safe to overwrite
    user_model.username = self.username
    user_model.password = self.password
    user_model.email = self.email
    user_model.first_name = self.first_name
    user_model.last_name = self.last_name
    user_model.role = self.role
    user_model.phone = self.phone
    return user_model