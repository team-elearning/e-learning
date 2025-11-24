import re
from typing import TypedDict, Optional, Dict, Any
from datetime import datetime, date

from custom_account.models import Profile


class ProfileDict(TypedDict):
    """Dataclass representing the ProfileSettings object."""
    user_id: int
    display_name: Optional[str]
    avatar_url: Optional[str]
    dob: Optional[datetime.date]
    gender: Optional[str] 
    language: str = "vi"
    meta: Optional[Dict[str, Any]]


class ProfileDomain:
    """Domain object aggregate data from Profile and User models."""

    def __init__(
        self,
        user_id: int,
        # --- Fields from Profile Model ---
        display_name: Optional[str] = None,
        avatar_id: Optional[str] = None,
        dob: Optional[date] = None,
        gender: Optional[str] = None,
        # --- Fields from User Model (New) ---
        username: str = "",
        email: str = "",
        role: str = "",
        phone: Optional[str] = None,
        is_active: bool = True,
        # --- Meta ---
        created_at: Optional[datetime] = None
    ):
        self.user_id = user_id
        self.display_name = display_name
        self.avatar_id = avatar_id
        self.dob = dob
        self.gender = gender
        
        # User info
        self.username = username
        self.email = email
        self.role = role
        self.phone = phone
        self.is_active = is_active
        
        self.created_at = created_at

    def validate(self):
        if self.user_id is None:
            raise ValueError("user_id is required")

        if isinstance(self.dob, datetime):
            self.dob = self.dob.date()

        if self.dob is not None and self.dob > date.today():
            raise ValueError("Date of birth cannot be in the future.")

        if self.language not in ["vietnamese", "english"]:
            raise ValueError("Unsupported language.")


    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "dob": self.dob,
            "gender": self.gender,
            "language": self.language,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProfileDomain":
        return cls(
            user_id=data["user_id"],
            display_name=data.get("display_name"),
            avatar_url=data.get("avatar_url"),
            dob=data.get("dob"),
            gender=data.get("gender"),
            language=data.get("language", "vi"),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_model(cls, model: Profile) -> "ProfileDomain":
        # Truy cập vào quan hệ user (model.user) để lấy data
        user = model.user 
        
        return cls(
            user_id=model.user_id,
            display_name=model.display_name,
            avatar_id=model.avatar_id,
            dob=model.dob,
            gender=model.gender,
            
            # Mapping từ bảng User sang Domain
            username=user.username,
            email=user.email,
            role=user.role,
            phone=user.phone,
            is_active=user.is_active,
            
            created_at=model.created_at
        )

    
    
    
