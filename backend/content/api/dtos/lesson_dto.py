import uuid
from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Any, Optional

from content.api.dtos.content_block_dto import ContentBlockCreateInput, ContentBlockUpdateInput, ContentBlockPublicOutput, ContentBlockAdminOutput



# =================================================================
# == Input DTOs 
# =================================================================

class LessonCreateInput(BaseModel):
    """
    DTO cho một Lesson lồng bên trong Module.
    """
    model_config = ConfigDict(from_attributes=True)

    title: str
    position: int = 0
    # content_type: str
    # published: bool = False
    content_blocks: List[ContentBlockCreateInput] = []


class LessonInput(BaseModel):
    """
    DTO để tạo một Lesson mới (cho POST/PUT).
    """
    title: str
    position: int | None = 0
    # content_type: str | None = "lesson"
    # published: bool | None = False

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)


class LessonUpdateInput(BaseModel):
    """DTO Input cho Lesson (PATCH)."""
    id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    # content_type: Optional[str] = None
    # published: Optional[bool] = None
    position: Optional[int] = None
    
    # Lồng nhau
    content_blocks: Optional[List[ContentBlockUpdateInput]] = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)


class LessonReorderInput(BaseModel):
    """
    DTO cho payload sắp xếp lại (reorder).
    """
    lesson_ids: List[uuid.UUID]

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)

# =================================================================
# == Output DTOs 
# =================================================================

class LessonPublicOutput(BaseModel):
    """
    DTO Output cho Lesson (lồng trong Module).
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    position: int
    # content_type: str
    # published: bool # Có thể bạn muốn public trường này
    content_blocks: List[ContentBlockPublicOutput] = []

    @field_validator('content_blocks', mode='before')
    @classmethod
    def convert_blocks_manager_to_list(cls, v: Any) -> list:
        if hasattr(v, 'all'):
            # return list(v.all().order_by('position'))
            return list(v.all())
        if isinstance(v, list):
            return v
        return []
    
    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)


class LessonAdminOutput(BaseModel):
    """
    DTO chứa đầy đủ các trường cho Admin/Instructor.
    Giống như UserAdminOutput.
    Sử dụng from_attributes=True để load từ Django Model.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    module_id: uuid.UUID  
    title: str
    position: int
    # content_type: str
    # published: bool
    content_blocks: List[ContentBlockAdminOutput] = []

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)