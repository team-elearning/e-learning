import uuid
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Any

from content.api.dtos.lesson_dto import LessonCreateInput, LessonUpdateInput, LessonPublicOutput, LessonAdminOutput



# ----------------------------------------------
# DTO cho việc TẠO MỚI (POST)
# ----------------------------------------------

class ModuleCreateInput(BaseModel):
    """
    DTO cho một Module lồng bên trong Course.
    """
    model_config = ConfigDict(from_attributes=True)

    title: str
    position: int = 0
    lessons: List[LessonCreateInput] = []


class ModuleInput(BaseModel):
    """
    DTO để tạo một Module mới.
    'course_id' sẽ được lấy từ URL, không cần nằm trong body.
    """
    title: Optional[str] = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_none=exclude_none)

# ----------------------------------------------
# DTO cho việc CẬP NHẬT (PATCH)
# ----------------------------------------------

class ModuleUpdateInput(BaseModel):
    """DTO Input cho Module (PATCH)."""
    id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None
    
    # Lồng nhau
    lessons: Optional[List[LessonUpdateInput]] = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_none=exclude_none)


# ----------------------------------------------
# DTO trả về cho PUBLIC
# ----------------------------------------------

class ModulePublicOutput(BaseModel):
    """
    DTO Output cho Module (lồng trong Course).
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    position: int
    lessons: List[LessonPublicOutput] = []

    @field_validator('lessons', mode='before')
    @classmethod
    def convert_lessons_manager_to_list(cls, v: Any) -> list:
        if hasattr(v, 'all'):
            # Có thể bạn muốn sắp xếp ở đây
            # return list(v.all().order_by('position'))
            return list(v.all()) 
        if isinstance(v, list):
            return v
        return []
    
    def to_dict(self, exclude_none: bool = True) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_none=exclude_none)


# ----------------------------------------------
# DTO trả về cho ADMIN
# ----------------------------------------------

class ModuleAdminOutput(BaseModel):
    """
    DTO Output cho Module (lồng trong Course).
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    position: int
    lessons: List[LessonAdminOutput] = []

    @field_validator('lessons', mode='before')
    @classmethod
    def convert_lessons_manager_to_list(cls, v: Any) -> list:
        if hasattr(v, 'all'):
            # Có thể bạn muốn sắp xếp ở đây
            # return list(v.all().order_by('position'))
            return list(v.all()) 
        if isinstance(v, list):
            return v
        return []
    
    def to_dict(self, exclude_none: bool = True) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_none=exclude_none)