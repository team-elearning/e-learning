import uuid
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List

from custom_account.api.dtos.user_dto import UserPublicOutput
from content.api.dtos.subject_dto import SubjectPublicOutput
from content.api.dtos.category_dto import CategoryOutput
from content.api.dtos.tag_dto import TagOutput



class CourseCreateInput(BaseModel):
    """
    DTO để TẠO một course (Giống UserInput).
    Chúng ta nhận ID cho các quan hệ.
    Owner sẽ được lấy từ request.user trong service.
    """
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    grade: str | None = None
    published: bool = False
    
    # Client gửi ID của các đối tượng liên quan
    subject_id: uuid.UUID | None = None
    category_ids: List[uuid.UUID] = []
    tag_ids: List[uuid.UUID] = []

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)


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


class CoursePublicOutput(BaseModel):
    """
    DTO public cho Course (Giống UserPublicOutput).
    Không chứa các trường nhạy cảm như 'published' hoặc 'owner'.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    grade: str | None
    
    # Giả sử model của bạn có 'created_on' và 'updated_on'
    # (Giống như UserAdminOutput của bạn)
    created_on: datetime | None = None
    updated_on: datetime | None = None

    # Trả về data đã lồng (nested)
    subject: SubjectPublicOutput | None = None
    categories: List[CategoryOutput] = []
    tags: List[TagOutput] = []

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)


class CourseAdminOutput(CoursePublicOutput):
    """
    DTO admin cho Course (Giống UserAdminOutput).
    Kế thừa từ Public và thêm các trường admin.
    """
    # model_config được kế thừa
    
    # Thêm các trường chỉ admin mới thấy
    published: bool
    owner: UserPublicOutput | None = None
    
    # Không cần `to_dict` vì đã được kế thừa