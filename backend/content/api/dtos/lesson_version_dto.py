from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID 

# ===================================================================
# DTOs cho CONTENT BLOCK (Entities con)
# ===================================================================

class ContentBlockInput(BaseModel):
    """
    DTO đầu vào cho một ContentBlock KHI TẠO/CẬP NHẬT.
    Nó nằm trong list 'content_blocks' của LessonVersionUpdateInput.
    """
    id: Optional[UUID] = None  # 👈 Rất quan trọng cho logic Cập nhật
    type: str
    position: int
    payload: Dict[str, Any] = {}

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)


class ContentBlockOutput(BaseModel):
    """
    DTO đầu ra (Output) cho một ContentBlock.
    Dùng 'from_attributes=True' để tự động đọc từ model/domain.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lesson_version_id: UUID
    type: str
    position: int
    payload: Dict[str, Any]

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)


# ===================================================================
# DTOs cho LESSON VERSION (Aggregate Root)
# ===================================================================

class LessonVersionInput(BaseModel):
    """
    DTO đầu vào (Input) khi TẠO MỚI (POST) một LessonVersion.
    Chỉ chứa các trường mà user được phép nhập lúc tạo.
    """
    change_summary: Optional[str] = None
    
    # User gửi lên một list các block (chưa có id)
    content_blocks: List[ContentBlockInput] = [] 

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)


class LessonVersionUpdateInput(BaseModel):
    """
    DTO đầu vào (Input) khi CẬP NHẬT (PATCH) một LessonVersion.
    Tất cả các trường đều là Optional.
    """
    change_summary: Optional[str] = None
    
    # Cho phép gửi cả list content_blocks mới để service xử lý
    content_blocks: Optional[List[ContentBlockInput]] = None 

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)


class LessonVersionOutput(BaseModel):
    """
    DTO đầu ra (Output) cho Admin/Instructor.
    Đây là DTO đầy đủ, đại diện cho toàn bộ "Cụm".
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lesson_id: UUID
    version: int
    status: str
    author_id: Optional[int] = None
    change_summary: Optional[str] = None
    created_at: datetime
    published_at: Optional[datetime] = None

    # Hiển thị cả 2:
    # 1. 'content' (bản cache JSON)
    # 2. 'content_blocks' (danh sách thực thể chi tiết)
    content: Dict[str, Any]
    content_blocks: List[ContentBlockOutput] = []

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)
    

class SetStatusInput(BaseModel):
    """
    DTO đầu vào (Input) cho hành động 'set_status'.
    Khớp với SetStatusSerializer.
    """
    status: str

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)