from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from uuid import UUID



class ProfileInput(BaseModel):
    display_name: str | None = None
    gender: str | None = None


class ProfileUpdateInput(BaseModel):
    # --- Profile Fields ---
    display_name: str | None = None
    avatar_id: UUID | None = None 
    dob: date | None = None
    gender: str | None = None
    
    # --- User Fields (New) ---
    username: str | None = Field(default=None, min_length=3)
    email: str | None = None
    phone: str | None = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)


class ProfilePublicOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # --- User Info (Mapped from Domain) ---
    username: str | None = None
    email: str | None = None
    role: str | None = None
    phone: str | None = None
    
    # --- Profile Info ---
    display_name: str | None = None
    avatar_id: str | None = None
    dob: date | None = None
    gender: str | None = None
    language: str | None = None
    metadata: dict | None = None
    created_at: datetime | None = None #

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        
        Args:
            exclude_none (bool): Whether to exclude keys with None values. Defaults to True.
        
        Returns:
            dict: A dictionary representation of the model.
        """
        return self.model_dump(exclude_none=exclude_none)
    

class ProfileAdminOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # --- User Info (Admin sees everything) ---
    user_id: UUID | int | str  # Chấp nhận nhiều loại ID (do model bạn dùng UUID)
    username: str
    email: str
    role: str
    phone: str | None = None
    is_active: bool | None = None # Admin cần thấy trạng thái kích hoạt
    
    # --- Profile Info ---
    display_name: str | None = None
    avatar_id: str | None = None
    dob: date | None = None
    gender: str | None = None
    language: str | None = None
    metadata: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None #

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        
        Args:
            exclude_none (bool): Whether to exclude keys with None values. Defaults to True.
        
        Returns:
            dict: A dictionary representation of the model.
        """
        return self.model_dump(exclude_none=exclude_none)