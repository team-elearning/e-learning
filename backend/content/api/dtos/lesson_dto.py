import uuid
from pydantic import BaseModel, ConfigDict, Field
from typing import List

# =================================================================
# == Input DTOs 
# =================================================================

class LessonInput(BaseModel):
    """
    DTO để tạo một Lesson mới (cho POST/PUT).
    """
    title: str
    position: int | None = 0
    content_type: str | None = "lesson"
    published: bool | None = False

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)

class LessonUpdateInput(BaseModel):
    """
    DTO để cập nhật (PATCH) một Lesson.
    Giống như UpdateUserInput, mọi trường đều là optional.
    """
    title: str | None = None
    position: int | None = None
    content_type: str | None = None
    published: bool | None = None

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
    DTO chứa các trường public cho Lesson.
    Giống như UserPublicOutput.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    module_id: uuid.UUID
    title: str
    position: int
    content_type: str
    published: bool

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
    content_type: str
    published: bool

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)