import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional

# ----------------------------------------------
# DTO cho việc TẠO MỚI (POST)
# ----------------------------------------------
class ModuleInput(BaseModel):
    """
    DTO để tạo một Module mới.
    'course_id' sẽ được lấy từ URL, không cần nằm trong body.
    """
    title: str
    position: Optional[int] = None  # Giống 'phone' là Optional, 
                                   # vì model có default=0

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_none=exclude_none)

# ----------------------------------------------
# DTO cho việc CẬP NHẬT (PATCH)
# ----------------------------------------------
class ModuleUpdateInput(BaseModel):
    """
    DTO để cập nhật một phần (PATCH) Module.
    Tất cả các trường đều là Optional.
    """
    title: str | None = None
    position: int | None = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_none=exclude_none)

# ----------------------------------------------
# DTO trả về cho PUBLIC
# ----------------------------------------------
class ModulePublicOutput(BaseModel):
    """
    Dữ liệu Module trả về cho người dùng public/thông thường.
    (Theo mẫu của bạn, sẽ không bao gồm ID).
    """
    title: str
    position: int

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_none=exclude_none)

# ----------------------------------------------
# DTO trả về cho ADMIN
# ----------------------------------------------
class ModuleAdminOutput(BaseModel):
    """
    Dữ liệu Module trả về cho Admin.
    Bao gồm ID, các khóa ngoại và dùng from_attributes 
    để map trực tiếp từ ORM model.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID  # Lấy từ 'module.course_id'
    title: str
    position: int
    
    # Module model không có 'created_on' hay 'is_active'
    # nên chúng ta không thêm vào đây.

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_none=exclude_none)