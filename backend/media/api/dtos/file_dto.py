# media/dtos.py
import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any

from media.models import FileStatus



# ==================================
# INPUT DTO
# ==================================
class FileInputDTO(BaseModel):
    """
    Pydantic DTO để cấu trúc hóa input *sau khi* DRF Serializer validate.
    """
    # 'file' sẽ là đối tượng InMemoryUploadedFile từ Django
    file: Any 
    content_type_str: Optional[str] = None
    object_id: Optional[int] = None
    component: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Chuyển DTO thành dict để gửi cho service."""
        # Bỏ trường 'file' ra khỏi model_dump nếu cần, 
        # nhưng ở đây chúng ta muốn cả file object
        return self.model_dump()

# ==================================
# OUTPUT DTO
# ==================================
class FileOutputDTO(BaseModel):
    """
    Pydantic DTO để serialize dữ liệu trả về cho client.
    Mixin sẽ dùng cái này.
    """
    # Yêu cầu Pydantic đọc attributes từ object (ví dụ: Django Model)
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    uploaded_at: datetime
    status: str # 'staging' hoặc 'committed'
    component: Optional[str] = None
    owner_id: uuid.UUID 
    
    # 'url' sẽ được đọc từ @property 'url' trên Model 'UploadedFile'
    url: str


# --- Update ---
class FileUpdateInputDTO(BaseModel):
    # Dùng Optional, vì đây là PATCH
    component: Optional[str] = None
    status: Optional[FileStatus] = None 
    # Thêm các trường khác bạn muốn cho phép cập nhật...
    
    class Config:
        use_enum_values = True