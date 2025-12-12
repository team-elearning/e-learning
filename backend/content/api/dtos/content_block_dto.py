import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, Literal



# Định nghĩa các loại block hợp lệ
BlockType = Literal['rich_text',  'video', 'quiz', 'pdf', 'docx', 'file', 'audio']

class ContentBlockCreateInput(BaseModel):
    """
    DTO cho một Content Block bên trong JSON.
    """
    model_config = ConfigDict(from_attributes=True)

    type: str
    payload: Dict[str, Any]


class ContentBlockInput(BaseModel):
    """
    DTO cho việc TẠO MỚI (POST) hoặc THAY THẾ (PUT) một ContentBlock.
    'position' được quản lý bởi service (tạo ở cuối hoặc reorder), 
    nên không cần đưa vào đây.
    """
    title: Optional[str]
    type: BlockType
    payload: Dict[str, Any] = {}

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)


class ContentBlockUpdateInput(BaseModel):
    """DTO Input cho ContentBlock (PATCH)."""
    id: Optional[uuid.UUID] = None
    type: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    position: Optional[int] = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)
    

# ==========================================
# PUBLIC INTERFACE (OUTPUT)
# ==========================================

class ContentBlockPublicOutput(BaseModel):
    """
    DTO Output cho Content Block.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: Optional[str]
    type: str
    position: int
    payload: Dict[str, Any] # Payload đã được chuẩn hóa (ví dụ: chứa quiz_id)
    icon_key: str | None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)


class ContentBlockAdminOutput(BaseModel):
    """
    DTO cho ADMIN/INSTRUCTOR.
    Giống hệt Public, nhưng thêm 'lesson_version_id'
    để tiện debug hoặc quản lý.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: Optional[str]
    type: BlockType
    position: int
    payload: Dict[str, Any]

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert the model to a dictionary.
        """
        return self.model_dump(exclude_none=exclude_none)