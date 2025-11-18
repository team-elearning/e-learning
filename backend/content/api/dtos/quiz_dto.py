import uuid
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import ConfigDict, field_serializer



# ---
# DTO CÂU HỎI (QUESTION)
# ---

class QuestionUpdateInput(BaseModel):
    """
    DTO cho một câu hỏi khi PATCH.
    Tất cả các trường là Optional.
    """
    id: Optional[uuid.UUID] = None # Key để service C/U/D
    type: Optional[str] = None
    position: Optional[int] = None
    prompt: Optional[Dict[str, Any]] = None
    answer_payload: Optional[Dict[str, Any]] = None
    hint: Optional[Dict[str, Any]] = None

# ---
# DTO BÀI QUIZ (QUIZ)
# ---

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
    answer_payload: Dict[str, Any]
    hint: Dict[str, Any]
    
    # Bạn không cần 'from_model' ở đây, 
    # Pydantic sẽ tự động map các trường từ model Question


class QuizPublicOutput(BaseModel):
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
    questions: List[QuestionPublicOutput] = []

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


class QuizAdminOutput(QuizPublicOutput):
    """
    DTO Output chi tiết cho Quiz (dành cho Admin).
    Hiện tại giống hệt Public, nhưng nên tách riêng
    để có thể mở rộng sau này (ví dụ: thêm thông tin owner).
    """
    pass