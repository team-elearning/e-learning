import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, Literal



# Định nghĩa các loại block hợp lệ
BlockType = Literal["text", "image", "video", "quiz", "exploration_ref"]


class ContentBlockInput(BaseModel):
    """
    DTO cho việc TẠO MỚI (POST) hoặc THAY THẾ (PUT) một ContentBlock.
    'position' được quản lý bởi service (tạo ở cuối hoặc reorder), 
    nên không cần đưa vào đây.
    """
    type: BlockType
    payload: Dict[str, Any] = {}

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)


class ContentBlockUpdateInput(BaseModel):
    """
    DTO cho việc CẬP NHẬT (PATCH) một ContentBlock.
    Tất cả các trường đều là optional.
    'position' bị cấm cập nhật trực tiếp qua service,
    phải dùng endpoint /reorder/, nên không có ở đây.
    """
    type: BlockType | None = None
    payload: Dict[str, Any] | None = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)
    

class ContentBlockPublicOutput(BaseModel):
    """
    DTO cho HỌC SINH (Public).
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    type: BlockType
    position: int
    payload: Dict[str, Any]


class ContentBlockAdminOutput(BaseModel):
    """
    DTO cho ADMIN/INSTRUCTOR.
    Giống hệt Public, nhưng thêm 'lesson_version_id'
    để tiện debug hoặc quản lý.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    lesson_version_id: uuid.UUID 
    type: BlockType
    position: int
    payload: Dict[str, Any]