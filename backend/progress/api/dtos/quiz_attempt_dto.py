from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime



# --- INPUT DTO ---
class StartQuizInput(BaseModel):
    """
    Dữ liệu đầu vào sạch để bắt đầu làm bài.
    """
    quiz_id: UUID

# --- OUTPUT DTOs ---

class QuizAttemptBaseOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True) # Cho phép map từ Object -> Pydantic
    
    id: UUID = Field(alias='attempt_id') # Map field 'id' của Domain thành 'attempt_id' JSON
    status: str
    started_at: datetime
    remaining_seconds: Optional[int] = None
    message: str

class QuizAttemptPublicOutput(QuizAttemptBaseOutput):
    """
    Output cho Học viên: Chỉ cần biết còn bao nhiêu giây và trạng thái.
    """
    pass

class QuizAttemptAdminOutput(QuizAttemptBaseOutput):
    """
    Output cho Admin/Giảng viên: Có thể thêm thông tin debug.
    """
    user_id: Optional[UUID] = None # Admin cần biết ai đang làm bài
    max_score: float # Admin cần check cấu hình điểm