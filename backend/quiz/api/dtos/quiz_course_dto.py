import uuid
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import ConfigDict, field_serializer

from content.api.dtos.question_dto import QuestionCreateInput, QuestionUpdateInput



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
class QuestionPublicOutput(BaseModel):
    """
    DTO Output cho một Câu hỏi (Question)
    Dùng để lồng vào QuizPublicOutput.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    position: int
    type: str
    prompt: Dict[str, Any]
    hint: Optional[Dict[str, Any]] = None
    
    # Bạn không cần 'from_model' ở đây, 
    # Pydantic sẽ tự động map các trường từ model Question


class QuizPublicOutput(BaseModel):
    """
    DTO Output chi tiết cho Quiz (dành cho Student).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    # Tự động lồng DTO Question con
    questions: List[QuestionPublicOutput] = []
    

class QuestionInstructorOutput(BaseModel):
    """
    DTO Output cho một Câu hỏi (Question)
    Dùng để lồng vào QuizPublicOutput.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    position: int
    type: str
    prompt: Dict[str, Any]
    answer_payload: Dict[str, Any]
    hint: Dict[str, Any]
    
    # Bạn không cần 'from_model' ở đây, 
    # Pydantic sẽ tự động map các trường từ model Question


class QuizInstructorOutput(BaseModel):
    """
    DTO Output chi tiết cho Quiz (dành cho Instructor/Public).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    time_limit: Optional[timedelta]
    time_open: Optional[datetime]
    time_close: Optional[datetime]
    
    # Tự động lồng DTO Question con
    questions: List[QuestionInstructorOutput] = []

    @field_serializer('time_limit')
    def serialize_time_limit(self, td: Optional[timedelta]) -> Optional[int]:
        """
        Chuyển đổi timedelta thành TỔNG SỐ GIÂY (dạng integer).
        Ví dụ: 30 phút -> 1800
        """
        if td is None:
            return None
        # Lấy tổng số giây (float) và ép kiểu về int
        return int(td.total_seconds())


class QuizAdminOutput(QuizInstructorOutput):
    """
    DTO Output chi tiết cho Quiz (dành cho Admin).
    Hiện tại giống hệt Public, nhưng nên tách riêng
    để có thể mở rộng sau này (ví dụ: thêm thông tin owner).
    """
    pass

