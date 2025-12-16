import uuid
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, Dict, Any, List

from progress.api.dtos.question_attempt_dto import QuizItemResultOutput



# # --- INPUT DTO ---
# class StartQuizInput(BaseModel):
#     """
#     Dữ liệu đầu vào sạch để bắt đầu làm bài.
#     """
#     quiz_id: UUID

# # --- OUTPUT DTOs ---

# class QuizAttemptBaseOutput(BaseModel):
#     model_config = ConfigDict(from_attributes=True) # Cho phép map từ Object -> Pydantic
    
#     id: UUID = Field(alias='attempt_id') # Map field 'id' của Domain thành 'attempt_id' JSON
#     status: str
#     started_at: datetime
#     remaining_seconds: Optional[int] = None
#     message: str

# class QuizAttemptPublicOutput(QuizAttemptBaseOutput):
#     """
#     Output cho Học viên: Chỉ cần biết còn bao nhiêu giây và trạng thái.
#     """
#     pass

# class QuizAttemptAdminOutput(QuizAttemptBaseOutput):
#     """
#     Output cho Admin/Giảng viên: Có thể thêm thông tin debug.
#     """
#     user_id: Optional[UUID] = None # Admin cần biết ai đang làm bài
#     max_score: float # Admin cần check cấu hình điểm


class QuizAttemptInfoOutput(BaseModel):
    """
    DTO trả về khi gọi POST init attempt.
    Chỉ chứa ID và danh sách ID câu hỏi (để vẽ thanh navigation 1,2,3...)
    """
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID = Field(alias="id") # Map từ QuizAttempt.id
    quiz_title: str 
    time_limit_seconds: Optional[int]
    time_start: datetime
    
    # Chỉ trả về List ID để client biết tổng số câu và thứ tự
    questions_order: List[str] 
    
    current_index: int = 0 # Resume lại vị trí cũ
    status: str

    @field_serializer('time_limit_seconds')
    def serialize_duration(self, v, _info):
        return v # Giả sử domain đã tính ra giây hoặc view xử lý
    

@dataclass
class QuizAttemptResultOutput(BaseModel):
    """ 
    DTO trả về cho Frontend hiển thị màn hình 'Kết quả bài thi'.
    Đã update để hứng toàn bộ computed fields từ Domain.
    """
    model_config = ConfigDict(from_attributes=True) # Pydantic v2 (orm_mode cũ)

    # === Identification ===
    id: uuid.UUID
    quiz_id: uuid.UUID          # Frontend cần cái này để làm nút "Thử lại" (Re-take)
    quiz_title: str             # Để hiển thị tiêu đề (Frontend đỡ phải query lại Quiz info)
    user_id: uuid.UUID

    # === Status & Time ===
    status: str
    is_finished: bool           # Helper từ Domain
    
    time_start: datetime
    completed_at: Optional[datetime] = None
    
    # === Duration Info ===
    # Frontend dùng 2 số này để hiển thị: "Làm trong 15 phút / 45 phút cho phép"
    time_limit_seconds: Optional[int] = None 
    time_taken_seconds: Optional[int] = 0

    # === Score Metrics ===
    score: float
    max_score: float
    percentage: float           # Quan trọng: Frontend dùng số này vẽ Circle/Bar chart
    is_passed: bool             # Quan trọng: Frontend dùng để hiện màu Xanh/Đỏ

    items: List[QuizItemResultOutput] = []

