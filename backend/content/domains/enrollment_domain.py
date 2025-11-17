# (Giả sử trong file domains.py)
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from content.models import Enrollment 



class EnrollmentDomain(BaseModel):
    """
    Domain Model (Pydantic) đại diện cho một Enrollment.
    Đây là "DTO" sạch mà service sẽ trả về.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    enrolled_at: datetime

    # Cho Pydantic v2: cho phép đọc từ attributes của model
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, enrollment_model: Enrollment) -> "EnrollmentDomain":
        """
        Factory method (Hàm khởi tạo) được yêu cầu:
        Tạo một instance EnrollmentDomain từ một instance Enrollment model.
        
        Chúng ta truy cập trực tiếp `_id` để tránh trigger lazy-load
        không cần thiết.
        """
        return cls(
            id=enrollment_model.id,
            user_id=enrollment_model.user_id,
            course_id=enrollment_model.course_id,
            enrolled_at=enrollment_model.enrolled_at
        )

    def to_dict(self) -> dict:
        """
        Hàm to_dict() được yêu cầu:
        Trong Pydantic, đây chính là hàm .model_dump()
        """
        return self.model_dump()