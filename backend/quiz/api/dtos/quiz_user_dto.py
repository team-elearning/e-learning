from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any, List, Dict

from quiz.api.dtos.exam_dto import ExamPublicOutput

# ==========================================
# HELPER MIXIN (Để tái sử dụng to_dict)
# ==========================================
class BaseDTO(BaseModel):
    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Standard conversion to dictionary
        """
        return self.model_dump(exclude_none=exclude_none)


# ==========================================
# Quiz Preflight Output (Màn hình chờ)
# ==========================================

class QuizAttemptStartInput(BaseModel):
    """
    Input DTO: Dữ liệu cần thiết để bắt đầu bài thi.
    (Moodle thường yêu cầu password ở đây nếu bài thi có pass)
    """
    password: Optional[str] = None 

    def to_dict(self):
        return self.model_dump()


# ==========================================
# Quiz Preflight Output (Màn hình chờ)
# ==========================================

# Access Decision DTO (Quyết định vào thi)
class AccessDecisionOutput(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    is_allowed: bool
    action: str  # 'start', 'resume', 'none'
    reason_message: str
    button_label: str
    ongoing_attempt_id: Optional[UUID] = None


# Attempt History DTO (Lịch sử thi)
class AttemptHistoryItemOutput(BaseModel):
    """DTO cho 1 dòng lịch sử"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    order: int
    status: str
    status_display: str = Field(validation_alias='status_label') # Map property 'status_label' từ domain
    score: Optional[float]
    time_submitted: Optional[datetime]


class QuizPreflightOutput(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    attempts_used: int
    score_best: float
    history: List[AttemptHistoryItemOutput]
    access_decision: AccessDecisionOutput
    exam: ExamPublicOutput


# ==========================================
# Quiz Attempt 
# ==========================================

class StartAttemptOutput(BaseModel):
    """Output DTO cho API POST /attempt/"""
    model_config = ConfigDict(from_attributes=True)
    
    attempt_id: UUID
    action: str
    detail: str
    

class QuestionTakingOutput(BaseModel):
    """
    DTO cho từng câu hỏi khi đang làm bài.
    Tuyệt đối không expose đáp án đúng.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    prompt: Dict[str, Any]
    
    # State phục vụ Resume & UX
    current_selection: Optional[Dict[str, Any]] = None
    is_answered: bool

class AttemptTakingOutput(BaseModel):
    """
    DTO Output cho API /student/attempts/<id>/
    """
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    quiz_title: str
    
    time_remaining_seconds: Optional[int] = Field(description="Số giây còn lại. Null nếu không giới hạn.")
    
    current_question_index: int
    total_questions: int
    
    questions: List[QuestionTakingOutput]


# ==========================================
# Quiz Save
# ==========================================

class SaveAnswerInput(BaseModel):
    """
    Input DTO cho hành động lưu bài.
    Chứa cả đáp án và trạng thái Flag.
    """
    question_id: UUID
    current_index: int
    
    # Optional vì có thể user chỉ muốn Flag mà không chọn đáp án (hoặc ngược lại)
    selected_options: Optional[Dict[str, Any]] = None 
    is_flagged: Optional[bool] = None

    def to_dict(self):
        return self.model_dump()
    

class SaveAnswerOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    status: str = "saved"
    saved_at: datetime
    