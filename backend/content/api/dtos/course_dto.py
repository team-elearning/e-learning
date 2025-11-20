import uuid
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Any, Optional
from pydantic import field_validator
from datetime import datetime

from content.api.dtos.subject_dto import SubjectPublicOutput, SubjectAdminOutput
from content.api.dtos.category_dto import CategoryOutput
from content.api.dtos.tag_dto import TagOutput
from content.api.dtos.module_dto import ModuleCreateInput, ModuleUpdateInput, ModulePublicOutput, ModuleAdminOutput



class CourseCreateInput(BaseModel):
    """
    DTO mới để TẠO một course từ cấu trúc JSON lồng nhau.
    """
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    grade: Optional[str] = None
    published: bool = False
    
    # === CÁC THAY ĐỔI QUAN TRỌNG ===
    
    # 1. Thêm image_url (từ JSON mẫu)
    image_id: Optional[str] = None

    # 2. Sửa categories (từ List[UUID] thành List[str])
    # JSON của bạn gửi ["Toán"], là list[str], không phải list[uuid]
    categories: List[str] = []
    tags: List[str] = []

    # 3. Thêm modules (DTO lồng nhau)
    modules: List[ModuleCreateInput] = []

    # 4. Giữ lại subject_id (giống DTO cũ của bạn, rất hợp lý)
    subject_id: Optional[uuid.UUID] = None
    
    # (Bạn có thể thêm 'tags: List[str] = []' ở đây nếu cần)

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)
    

class CourseUpdateInput(BaseModel):
    """
    DTO Input chính cho PATCH.
    MỌI TRƯỜNG đều là 'Optional'.
    """
    title: Optional[str] = None
    image_id: Optional[str] = None
    description: Optional[str] = None
    
    # Thêm trường 'subject'
    subject: Optional[uuid.UUID] = None

    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    
    grade: Optional[str] = None
    published: Optional[bool] = None
    
    # Lồng nhau
    modules: Optional[List[ModuleUpdateInput]] = None


class CoursePublicOutput(BaseModel):
    """
    DTO Output cho TOÀN BỘ cấu trúc khóa học.
    Kế thừa từ DTO public của bạn và thêm modules.
    """
    model_config = ConfigDict(from_attributes=True)

    # --- Các trường metadata (giống DTO của bạn) ---
    id: uuid.UUID
    title: str
    description: Optional[str]
    grade: Optional[str]
    
    # Giả sử bạn muốn public các trường này
    image_url: Optional[str] = None
    subject: Optional[SubjectPublicOutput] = None
    slug: str
    categories: List[str] = Field(default=[], alias="category_names")
    tags: List[str] = Field(default=[], alias="tag_names")
    
    # --- THÊM CẤU TRÚC LỒNG NHAU ---
    modules: List[ModulePublicOutput] = []

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)
    

    @field_validator('categories', 'tags', 'modules', mode='before')
    @classmethod
    def convert_manager_to_list(cls, v: Any) -> list:
        if hasattr(v, 'all'):
            return list(v.all())
        if isinstance(v, list):
            return v
        return []
    

class CourseAdminOutput(BaseModel):
    """
    DTO Output cho Admin/Instructor.
    Bao gồm TOÀN BỘ cấu trúc khóa học và các metadata quản trị.
    """
    model_config = ConfigDict(from_attributes=True)

    # --- Các trường Metadata (giống Public) ---
    id: uuid.UUID
    title: str
    description: Optional[str]
    grade: Optional[str]
    slug: str
    image_url: Optional[str] = None
    
    # --- Các trường quản trị (Admin-only) ---
    published: bool
    published_at: Optional[datetime] = None # Thêm trường này từ domain
    
    # Thông tin chi tiết về chủ sở hữu
    owner_id: uuid.UUID
    
    # --- Các quan hệ (Sử dụng DTO đầy đủ) ---
    subject: Optional[SubjectAdminOutput] = None
    
    # Admin cần DTO đầy đủ (CategoryOutput) chứ không phải List[str]
    categories: List[CategoryOutput] = [] 
    tags: List[TagOutput] = []
    
    # --- Cấu trúc khóa học lồng nhau (Giống Public) ---
    # Giả sử ModulePublicOutput đã bao gồm lessons, v.v.
    modules: List[ModuleAdminOutput] = []

    # --- Validator (Rất quan trọng) ---
    @field_validator('categories', 'tags', 'modules', mode='before')
    @classmethod
    def convert_manager_to_list(cls, v: Any) -> list:
        """
        Chuyển đổi Django RelatedManager (ví dụ: model.tags) 
        thành một list trước khi Pydantic validate.
        Điều này rất quan trọng khi dùng from_attributes=True
        """
        if hasattr(v, 'all'):
            # Đây là một Manager (ví dụ: course.modules.all())
            return list(v.all())
        if isinstance(v, list):
            # Đây đã là một list (ví dụ: từ CourseDomain)
            return v
        # Trả về list rỗng nếu không có gì
        return []

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Helper để chuyển đổi DTO sang dict, bỏ qua các giá trị None."""
        return self.model_dump(exclude_none=exclude_none)
    




