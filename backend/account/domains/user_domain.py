import re
from typing import TypedDict, Optional
from datetime import datetime, timezone

from account.models import UserModel


class UserDict(TypedDict):
    """Dataclass representing the UserSettings object."""
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str] 
    created_on: datetime
    role: str 
    phone: Optional[str]


class UserDomain:
    """Value object representing a user's settings.
    Attributes:
        id: int | None. Unique identifier of the user (from DB).
        username: str. The unique of the user. Identifiable username to display in the UI.
        email: str. The user email.
        first_name: str. The first name of the user.
        last_name: str. The last name of the user.
        created_on: datetime. The date and time when the user was created.
        role: str. Role of the user.
        phone: str. The phone number of the user.
    """

    PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.[A-Z])(?=.*\d).{8,}$')

    def __init__(self, username: str, email: str, id: int | None= None, 
                 first_name: Optional[str] = None, last_name: Optional[str] = None, 
                 created_on: Optional[datetime] = None,
                 role: str = "student", phone: Optional[str] = None):
        self.id = id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.created_on = created_on 
        self.role = role
        self.phone = phone


    # --- Validation ---
    def validate(self):
        """Validate the UserDomain object.
        Raises:
            ValueError: If any of the required attributes are missing or invalid.
        """
        if not self.username:
            raise ValueError("Username is required.")
        
        if not self.email:
            raise ValueError("Email is required.")
        # Basic email format check
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
            raise ValueError("Invalid email format.")
        
        if self.role not in ["student", "instructor", "admin"]:
            raise ValueError("Role must be one of 'student', 'instructor', or 'admin'.")


    # --- Serialization ---
    def to_dict(self) -> UserDict: # domain to dict 
        """Convert the UserDomain object to a dictionary.
        Returns:
            dict. The dictionary representation of the UserDomain object.
        """
        return {
            'id': self.id,
            'username':self.username,
            'email':self.email,
            'first_name':self.first_name,
            'last_name':self.last_name,
            'created_on':self.created_on,
            'role':self.role,
            'phone':self.phone
        }
    
    @classmethod
    def from_dict(cls, data: UserDict) -> "UserDomain": # dict to domain
        """Create a UserDomain object from a dictionary.
        Args:
            data: dict. The dictionary representation of the UserDomain object.
        Returns:
            UserDomain. The UserDomain object created from the dictionary.
        """
        return cls(
            id=data.get('id'),
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            created_on=data.get('created_on'),
            role=data.get('role', 'student'),
            phone=data.get('phone')
        )
    

    # --- Mapping methods ---
    @classmethod
    def from_model(cls, user_model:UserModel) -> "UserDomain": # model -> domain
        """Convert a UserModel instance → UserDomain."""
        return cls(
            id=user_model.id,
            username=user_model.username,
            email=user_model.email,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            phone=user_model.phone,
            role=user_model.role,
            created_on=user_model.created_on,
        )
    

    # --- Helpers ---
    @property
    def full_name(self) -> str:
        """Get the full name of the user.
        Returns:
            str. The full name of the user.
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or ""
    
    # def update_password(self, new_password: str) -> None:
    #     """Change the user's password.
    #     Args:
    #         new_password: str. The new password for the user.
    #     Raises:
    #         ValueError: If the new password is invalid.
    #     """
    #     # Basic password complexity check: at least 8 characters, one uppercase, one lowercase, one digit
    #     if not re.match(self.PASSWORD_PATTERN, new_password):
    #         raise ValueError("Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, and one digit.")
        
    #     self.password = new_password



class LoginDomain:
    """Value object representing a login attempt.
    
    Attributes:
        username_or_email: str. The username or email of the user.
        password: str. The plain-text password entered by the user.
    """

    def __init__(self, username_or_email: str, raw_password: str):
        self.username_or_email = username_or_email
        self.raw_password = raw_password
        self.validate()

    def validate(self) -> None:
        if not self.username_or_email:
            raise ValueError("Username or email is required.")
        if not self.raw_password:
            raise ValueError("Password is required.")
        
    def to_dict(self) -> dict: # used internally in service layer, not for API response
        return {
            "username_or_email": self.username_or_email,
            "raw_password": self.raw_password,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "LoginDomain": 
        return cls(
            username_or_email = data["username_or_email"],
            raw_password = data["raw_password"],
        )


    

