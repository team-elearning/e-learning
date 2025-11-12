from typing import Optional
from pydantic import BaseModel, ConfigDict
import uuid

class CategoryInput(BaseModel):
    name: str
    slug: str

class UpdateCategoryInput(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None

class CategoryOutput(BaseModel):
    """DTO cho Category (để lồng vào Course output)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID # Giả định Category dùng UUID
    name: str # Giả định Category có trường 'name'
    slug: str

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)
