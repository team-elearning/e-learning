import uuid
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from pydantic import field_validator
from datetime import datetime, timedelta


from custom_account.api.dtos.user_dto import UserAdminOutput
from content.api.dtos.subject_dto import SubjectPublicOutput, SubjectAdminOutput
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
class QuestionCreateInput(BaseModel):
    """DTO cho một câu hỏi (lồng trong Quiz)"""
    id: Optional[uuid.UUID] = None # Dùng cho patch
    type: str
    position: int
    prompt: Dict[str, Any] = {}
    answer_payload: Dict[str, Any] = {}
    hint: Optional[Dict[str, Any]] = None


class QuizCreateInput(BaseModel):
    """
    DTO cho payload của 'quiz'.
    ĐÂY LÀ NƠI CẦN SỬA.
    """
    title: str
    
    # === SỬA DÒNG NÀY ===
    # Chuyển từ 'int' hoặc 'str' sang 'timedelta'
    time_limit: Optional[timedelta] = None
    # === KẾT THÚC SỬA ===
    
    time_open: Optional[datetime] = None
    time_close: Optional[datetime] = None
    questions: List[QuestionCreateInput] = []


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
    

class ModuleAdminOutput(BaseModel):
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
    owner: UserAdminOutput 
    
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
    

class ContentBlockUpdateInput(BaseModel):
    """DTO Input cho ContentBlock (PATCH)."""
    id: Optional[uuid.UUID] = None
    type: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    position: Optional[int] = None

class LessonUpdateInput(BaseModel):
    """DTO Input cho Lesson (PATCH)."""
    id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    content_type: Optional[str] = None
    published: Optional[bool] = None
    position: Optional[int] = None
    
    # Lồng nhau
    content_blocks: Optional[List[ContentBlockUpdateInput]] = None

class ModuleUpdateInput(BaseModel):
    """DTO Input cho Module (PATCH)."""
    id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None
    
    # Lồng nhau
    lessons: Optional[List[LessonUpdateInput]] = None


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