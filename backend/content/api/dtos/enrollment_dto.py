from pydantic import BaseModel, ConfigDict
from typing import List
import uuid
from datetime import datetime



class EnrollmentInput(BaseModel):
    """
    DTO Input tương ứng cho việc Enroll
    """
    user_id: uuid.UUID

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)


class EnrollmentOutput(BaseModel):
    """
    Output DTO: Map 1-1 với Domain (nhưng là Pydantic để dễ convert dict)
    Chỉ trả về IDs theo đúng yêu cầu.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    enrolled_at: datetime

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)
    

class EnrollmentListOutput(BaseModel):
    """
    DTO bao bọc danh sách để trả về kèm metadata (số lượng).
    """
    model_config = ConfigDict(from_attributes=True)

    total_count: int
    instance: List[EnrollmentOutput]

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)