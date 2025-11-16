import uuid
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from pydantic import field_validator


from custom_account.api.dtos.user_dto import UserPublicOutput
from content.api.dtos.subject_dto import SubjectPublicOutput
from content.api.dtos.category_dto import CategoryOutput
from content.api.dtos.tag_dto import TagOutput



# class CourseCreateInput(BaseModel):
#     """
#     DTO để TẠO một course (Giống UserInput).
#     Chúng ta nhận ID cho các quan hệ.
#     Owner sẽ được lấy từ request.user trong service.
#     """
#     title: str = Field(..., min_length=3, max_length=255)
#     description: str | None = None
#     grade: str | None = None
#     published: bool = False
    
#     # Client gửi ID của các đối tượng liên quan
#     subject_id: uuid.UUID | None = None
#     category_ids: List[uuid.UUID] = []
#     tag_ids: List[uuid.UUID] = []

#     def to_dict(self, exclude_none: bool = True) -> dict:
#         return self.model_dump(exclude_none=exclude_none)


class CourseUpdateInput(BaseModel):
    """
    DTO để CẬP NHẬT (PATCH) một course (Giống UpdateUserInput).
    Tất cả các trường đều là Optional.
    """
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    grade: str | None = None
    published: bool | None = None
    
    # None = không thay đổi
    # [] = xoá hết
    subject_id: uuid.UUID | None = None
    category_ids: List[uuid.UUID] | None = None
    tag_ids: List[uuid.UUID] | None = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)


# class CoursePublicOutput(BaseModel):
#     """
#     DTO public cho Course (Giống UserPublicOutput).
#     Không chứa các trường nhạy cảm như 'published' hoặc 'owner'.
#     """
#     model_config = ConfigDict(from_attributes=True)

#     id: uuid.UUID
#     title: str
#     description: str | None
#     grade: str | None
    
#     # Giả sử model của bạn có 'created_on' và 'updated_on'
#     # (Giống như UserAdminOutput của bạn)
#     created_on: datetime | None = None
#     updated_on: datetime | None = None

#     # Trả về data đã lồng (nested)
#     subject: SubjectPublicOutput | None = None
#     categories: List[CategoryOutput] = []
#     tags: List[TagOutput] = []

#     def to_dict(self, exclude_none: bool = True) -> dict:
#         return self.model_dump(exclude_none=exclude_none)


# class CourseAdminOutput(CoursePublicOutput):
#     """
#     DTO admin cho Course (Giống UserAdminOutput).
#     Kế thừa từ Public và thêm các trường admin.
#     """
#     # model_config được kế thừa
    
#     # Thêm các trường chỉ admin mới thấy
#     published: bool
#     owner: UserPublicOutput | None = None
    
#     # Không cần `to_dict` vì đã được kế thừa

####################################################################################################################################################
class ContentBlockCreateInput(BaseModel):
    """
    DTO cho một Content Block bên trong JSON.
    """
    model_config = ConfigDict(from_attributes=True)

    type: str
    position: int = 0
    # Payload đã được DRF Serializer validate, 
    # nên ở đây chỉ cần nhận là một dict
    payload: Dict[str, Any]

class LessonCreateInput(BaseModel):
    """
    DTO cho một Lesson lồng bên trong Module.
    """
    model_config = ConfigDict(from_attributes=True)

    title: str
    position: int = 0
    content_type: str
    published: bool = False
    content_blocks: List[ContentBlockCreateInput] = []

class ModuleCreateInput(BaseModel):
    """
    DTO cho một Module lồng bên trong Course.
    """
    model_config = ConfigDict(from_attributes=True)

    title: str
    position: int = 0
    lessons: List[LessonCreateInput] = []


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
    image_url: Optional[str] = None

    # 2. Sửa categories (từ List[UUID] thành List[str])
    # JSON của bạn gửi ["Toán"], là list[str], không phải list[uuid]
    categories: List[str] = []

    # 3. Thêm modules (DTO lồng nhau)
    modules: List[ModuleCreateInput] = []

    # 4. Giữ lại subject_id (giống DTO cũ của bạn, rất hợp lý)
    subject_id: Optional[uuid.UUID] = None
    
    # (Bạn có thể thêm 'tags: List[str] = []' ở đây nếu cần)

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)
    


class SubjectPublicOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str

class CategoryOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str

class TagOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str

# --- DTO Output cho cấu trúc lồng nhau ---

class ContentBlockPublicOutput(BaseModel):
    """
    DTO Output cho Content Block.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    type: str
    position: int
    payload: Dict[str, Any] # Payload đã được chuẩn hóa (ví dụ: chứa quiz_id)

class LessonPublicOutput(BaseModel):
    """
    DTO Output cho Lesson (lồng trong Module).
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    position: int
    content_type: str
    published: bool # Có thể bạn muốn public trường này
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


# (Tiếp theo các class ở trên)

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
    subject: Optional[SubjectPublicOutput] = None
    categories: List[CategoryOutput] = []
    tags: List[TagOutput] = []

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
    # --- THÊM DÒNG NÀY ---
    model_config = ConfigDict(from_attributes=True) 

    # (Các trường của Admin DTO...)
    id: uuid.UUID
    title: str
    published: bool
    owner: UserPublicOutput # Giả sử
    
    # Các trường này chính là 3 trường gây lỗi
    categories: List[CategoryOutput]
    tags: List[TagOutput]
    modules: List[ModulePublicOutput]