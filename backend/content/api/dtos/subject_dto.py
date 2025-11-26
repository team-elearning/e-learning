from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID  # Subject dùng UUID làm PK thay vì int

#
# 1. DTOs cho Input (Tạo & Cập nhật)
#

class SubjectInput(BaseModel):
    """
    DTO để tạo một Subject mới (POST).
    Slug là không bắt buộc vì service có thể tự tạo từ title.
    """
    title: str
    slug: str | None = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Chuyển đổi model sang dictionary."""
        return self.model_dump(exclude_none=exclude_none)


class UpdateSubjectInput(BaseModel):
    """
    DTO để cập nhật từng phần một Subject (PATCH).
    Tất cả các trường đều là tùy chọn.
    """
    title: str | None = None
    slug: str | None = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Chuyển đổi model sang dictionary."""
        return self.model_dump(exclude_none=exclude_none)


#
# 2. DTOs cho Output (Serialization)
#

class SubjectPublicOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    slug: str

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Chuyển đổi model sang dictionary."""
        return self.model_dump(exclude_none=exclude_none)


class SubjectAdminOutput(BaseModel):
    """
    DTO hiển thị Subject cho người dùng 'admin'.
    Tuân theo mẫu của UserAdminOutput (bao gồm tất cả các trường).
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID  # Subject dùng UUID
    title: str
    slug: str

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Chuyển đổi model sang dictionary."""
        return self.model_dump(exclude_none=exclude_none)