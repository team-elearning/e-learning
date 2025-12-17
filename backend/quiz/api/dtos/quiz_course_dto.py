import uuid
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import ConfigDict, field_serializer

from content.api.dtos.question_dto import QuestionCreateInput, QuestionUpdateInput
from quiz.api.dtos.question_dto import QuestionPublicOutput, QuestionInstructorOutput, QuestionAdminOutput



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


class QuizUpdateInput(BaseModel):
    """
    DTO cho body của request PATCH.
    Dùng trong QuizDetailView để gọi model_dump(exclude_unset=True).
    """
    title: Optional[str] = None
    
    # Pydantic sẽ tự động parse chuỗi "HH:MM:SS" (từ Serializer)
    # thành timedelta cho bạn.
    time_limit: Optional[timedelta] = None
    
    time_open: Optional[datetime] = None
    time_close: Optional[datetime] = None
    
    # Mảng questions lồng nhau
    questions: Optional[List[QuestionUpdateInput]] = None


# ------------------------
# OUTPUT DTOs
# ------------------------
class QuizPublicOutput(BaseModel):
    """
    DTO Output chi tiết cho Quiz (dành cho Student).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    # Tự động lồng DTO Question con
    questions: List[QuestionPublicOutput] = []


class QuizInstructorOutput(BaseModel):
    """
    DTO Output chi tiết cho Quiz (dành cho Admin).
    Hiện tại giống hệt Public, nhưng nên tách riêng
    để có thể mở rộng sau này (ví dụ: thêm thông tin owner).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    # Tự động lồng DTO Question con
    questions: List[QuestionInstructorOutput] = []
    owner_id: Optional[uuid.UUID]
    owner_name: Optional[str]

    
class QuizAdminOutput(QuizPublicOutput):
    """
    DTO Output chi tiết cho Quiz (dành cho Admin).
    Hiện tại giống hệt Public, nhưng nên tách riêng
    để có thể mở rộng sau này (ví dụ: thêm thông tin owner).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    # Tự động lồng DTO Question con
    questions: List[QuestionAdminOutput] = []
    owner_id: Optional[uuid.UUID]
    owner_name: Optional[str]

