import uuid
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Any, Optional, Dict
from pydantic import field_validator
from datetime import datetime

from content.api.dtos.subject_dto import SubjectPublicOutput, SubjectAdminOutput
from content.api.dtos.category_dto import CategoryOutput
from content.api.dtos.tag_dto import TagOutput
from content.api.dtos.module_dto import ModuleCreateInput, ModuleUpdateInput, ModulePublicOutput, ModuleAdminOutput



class CourseMetadataCreateInput(BaseModel):
    """
    DTO mới để TẠO một course từ cấu trúc JSON lồng nhau.
    """

    title: str = Field(min_length=2, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    subject: Optional[str] = None
    description: Optional[str] = None
    grade: Optional[str] = None
    published: bool = False
    
    # M2M relationships
    categories: List[str] = []
    tags: List[str] = []

    # File reference
    image_id: Optional[str] = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)
    

class CourseTemplateCreateInput(BaseModel):
    """
    DTO mới để TẠO một course từ cấu trúc JSON lồng nhau.
    """

    title: str = Field(min_length=3, max_length=255)
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
    

class CourseMetadataUpdateInput(BaseModel):
    """
    DTO mới để TẠO một course từ cấu trúc JSON lồng nhau.
    """

    title: Optional[str] = Field(None, min_length=2, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    subject: Optional[str] = None
    description: Optional[str] = None
    grade: Optional[str] = None
    published: Optional[bool] = None
    
    # M2M relationships
    categories: Optional[List[str]] = []
    tags: Optional[List[str]] = []

    # File reference
    image_id: Optional[str] = None

    def to_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


# class CourseUpdateInput(BaseModel):
#     """
#     DTO Input chính cho PATCH.
#     MỌI TRƯỜNG đều là 'Optional'.
#     """
#     title: Optional[str] = None
#     image_id: Optional[str] = None
#     description: Optional[str] = None
    
#     # Thêm trường 'subject'
#     subject: Optional[str] = None

#     categories: Optional[List[str]] = None
#     tags: Optional[List[str]] = None
    
#     grade: Optional[str] = None
#     published: Optional[bool] = None
    
#     # Lồng nhau
#     modules: Optional[List[ModuleUpdateInput]] = None


# ==========================================
# PUBLIC INTERFACE (OUTPUT)
# ==========================================

class CourseCatalogPublicOutput(BaseModel):
    """
    DTO Output cho TOÀN BỘ cấu trúc khóa học.
    Kế thừa từ DTO public của bạn và thêm modules.
    """
    model_config = ConfigDict(from_attributes=True)

    # --- Các trường metadata (giống DTO của bạn) ---
    id: uuid.UUID
    title: str
    slug: str
    description: Optional[str]
    short_description: Optional[str]

    price: Optional[str]
    currency: Optional[str]
    is_free: bool
    published: bool
    grade: Optional[str]
    
    owner_name: Optional[str]
    subject: Optional[SubjectPublicOutput]

    categories: List[CategoryOutput] = [] 
    tags: List[TagOutput] = []

    thumbnail_url: Optional[str]
    
    # --- THÊM CẤU TRÚC LỒNG NHAU ---
    stats: Optional[Dict]

    updated_at: Optional[datetime] = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)
    

class CourseCatalogInstructorOutput(BaseModel):
    """
    DTO Output cho Instructor.
    Bao gồm TOÀN BỘ cấu trúc khóa học và các metadata quản trị.
    """
    model_config = ConfigDict(from_attributes=True)

    # --- Các trường Metadata (giống Public) ---
    id: uuid.UUID
    title: str
    slug: str
    description: Optional[str]
    short_description: Optional[str]

    price: Optional[str]
    currency: Optional[str]
    is_free: bool
    published: bool
    grade: Optional[str]

    owner_id: uuid.UUID | None = None
    owner_name: Optional[str]
    subject: Optional[SubjectPublicOutput]

    categories: List[CategoryOutput] = [] 
    tags: List[TagOutput] = []

    thumbnail_url: Optional[str]

    stats: Optional[Dict]
    
    published_at: Optional[datetime] = None 
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Helper để chuyển đổi DTO sang dict, bỏ qua các giá trị None."""
        return self.model_dump(exclude_none=exclude_none)
    

class CourseCatalogAdminOutput(BaseModel):
    """
    DTO Output cho Admin/Instructor.
    Bao gồm TOÀN BỘ cấu trúc khóa học và các metadata quản trị.
    """
    model_config = ConfigDict(from_attributes=True)

    # --- Các trường Metadata (giống Public) ---
    id: uuid.UUID
    title: str
    slug: str
    description: Optional[str]
    short_description: Optional[str]

    price: Optional[str]
    currency: Optional[str]
    is_free: bool
    published: bool
    grade: Optional[str]

    owner_id: uuid.UUID | None = None
    owner_name: Optional[str]
    subject: Optional[SubjectAdminOutput]

    categories: List[CategoryOutput] = [] 
    tags: List[TagOutput] = []

    thumbnail_url: Optional[str]

    stats: Optional[Dict]
    
    published_at: Optional[datetime] = None # Thêm trường này từ domain
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Helper để chuyển đổi DTO sang dict, bỏ qua các giá trị None."""
        return self.model_dump(exclude_none=exclude_none)


class CoursePublicOutput(BaseModel):
    """
    DTO Output cho TOÀN BỘ cấu trúc khóa học.
    Kế thừa từ DTO public của bạn và thêm modules.
    """
    model_config = ConfigDict(from_attributes=True)

    # --- Các trường metadata (giống DTO của bạn) ---
    id: uuid.UUID
    title: str
    slug: str
    description: Optional[str]
    short_description: Optional[str]

    price: Optional[str]
    currency: Optional[str]
    is_free: bool
    published: bool
    grade: Optional[str]

    owner_id: uuid.UUID | None = None
    owner_name: Optional[str]
    subject: Optional[SubjectPublicOutput]
    
    categories: List[CategoryOutput] = [] 
    tags: List[TagOutput] = []

    thumbnail_url: Optional[str]

    stats: Optional[Dict]

    updated_at: Optional[datetime] = None
    
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


class CourseInstructorOutput(BaseModel):
    """
    DTO Output cho Admin/Instructor.
    Bao gồm TOÀN BỘ cấu trúc khóa học và các metadata quản trị.
    """
    model_config = ConfigDict(from_attributes=True)

    # --- Các trường Metadata (giống Public) ---
    id: uuid.UUID
    title: str
    slug: str
    description: Optional[str]
    short_description: Optional[str]

    price: Optional[str]
    currency: Optional[str]
    is_free: bool
    published: bool
    grade: Optional[str]
    
    owner_id: uuid.UUID | None = None
    owner_name: Optional[str]
    subject: Optional[SubjectPublicOutput]
    
    categories: List[CategoryOutput] = [] 
    tags: List[TagOutput] = []

    thumbnail_url: Optional[str]

    stats: Optional[Dict]

    published_at: Optional[datetime] = None # Thêm trường này từ domain
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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


class CourseAdminOutput(BaseModel):
    """
    DTO Output cho Admin/Instructor.
    Bao gồm TOÀN BỘ cấu trúc khóa học và các metadata quản trị.
    """
    model_config = ConfigDict(from_attributes=True)

    # --- Các trường Metadata (giống Public) ---
    id: uuid.UUID
    title: str
    slug: str
    description: Optional[str]
    short_description: Optional[str]

    price: Optional[str]
    currency: Optional[str]
    is_free: bool
    published: bool
    grade: Optional[str]
    
    owner_id: uuid.UUID | None = None
    owner_name: Optional[str]
    subject: Optional[SubjectPublicOutput]
    
    categories: List[CategoryOutput] = [] 
    tags: List[TagOutput] = []

    thumbnail_url: Optional[str]

    stats: Optional[Dict]

    published_at: Optional[datetime] = None # Thêm trường này từ domain
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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
    




