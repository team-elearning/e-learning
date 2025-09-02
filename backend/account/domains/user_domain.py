from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
import re

@dataclass
class UserDict():
    """Dataclass representing the UserSettings object."""
    username: str
    password: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_on: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    role: str = 'student'
    phone: Optional[str] = None

class UserDomain:
    """Value object representing a user's settings.
    Attributes:
        user_name: str. The unique of the user. Identifiable username to display in the UI.
        password: str. The hashed password of the user.
        email: str. The user email.
        first_name: str. The first name of the user.
        last_name: str. The last name of the user.
        created_on: datetime. The date and time when the user was created.
        role: str. Role of the user.
        phone: str. The phone number of the user.
    """
    def __init__(self, user_name: str, password: str, email: str, first_name: Optional[str] = None,
                 last_name: Optional[str] = None, created_on: Optional[datetime.datetime] = None,
                 role: str = 'student', phone: Optional[str] = None):
        self.user_name = user_name
        self.password = password
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.created_on = created_on
        self.role = role
        self.phone = phone

    def validate(self) -> None:
        """Validate the UserDomain object.
        Raises:
            ValueError: If any of the required attributes are missing or invalid.
        """
        if not self.user_name:
            raise ValueError("Username is required.")
        
        if not self.password:
            raise ValueError("Password is required.")
        # Basic password complexity check: at least 8 characters, one uppercase, one lowercase, one digit
        password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')
        if not re.match(password_pattern, self.password):
            raise ValueError("Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, and one digit.")

        if not self.email:
            raise ValueError("Email is required.")
        # Basic email format check
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
            raise ValueError("Invalid email format.")
        
        if self.role not in ['student', 'instructor', 'admin']:
            raise ValueError("Role must be one of 'student', 'instructor', or 'admin'.")

    def to_dict(self) -> UserDict:
        """Convert the UserDomain object to a dictionary.
        Returns:
            dict. The dictionary representation of the UserDomain object.
        """
        return UserDict(
            username=self.user_name,
            password=self.password,
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            created_on=self.created_on,
            role=self.role,
            phone=self.phone
        )
    
    @classmethod
    def from_dict(cls, data: UserDict) -> 'UserDomain':
        """Create a UserDomain object from a dictionary.
        Args:
            data: dict. The dictionary representation of the UserDomain object.
        Returns:
            UserDomain. The UserDomain object created from the dictionary.
        """
        return cls(
            user_name=data['username'],
            password=data['password'],
            email=data['email'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            created_on=data.get('created_on'),
            role=data.get('role', 'student'),
            phone=data.get('phone')
        )
    
    @property
    def full_name(self) -> str:
        """Get the full name of the user.
        Returns:
            str. The full name of the user.
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return ""
    
    @property
    def change_password(self, new_password: str) -> None:
        """Change the user's password.
        Args:
            new_password: str. The new password for the user.
        Raises:
            ValueError: If the new password is invalid.
        """
        # Basic password complexity check: at least 8 characters, one uppercase, one lowercase, one digit
        password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')
        if not re.match(password_pattern, new_password):
            raise ValueError("Password must be at least 8 characters long and include at least one uppercase letter, one lowercase letter, and one digit.")
        
        self.password = new_password


    

