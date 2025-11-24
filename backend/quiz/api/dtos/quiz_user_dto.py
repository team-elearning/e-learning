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
    is_flagged: Optional[bool] = None

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

    def to_dict(self, exclude_none: bool = True) -> dict:
        """Convert DTO to Dict to pass into Service"""
        return self.model_dump(exclude_none=exclude_none)
    

class SaveAnswerOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    status: str = "saved"
    saved_at: datetime


# ==========================================
# Quiz Submit
# ==========================================

class SubmitOutput(BaseModel):
    """
    DTO trả về cho Client sau khi nộp bài thành công.
    """
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    status: str

    correct_count: int = Field(..., description="Số câu trả lời đúng")
    total_questions: int = Field(..., description="Tổng số câu hỏi")

    score_obtained: float = Field(..., description="Điểm đạt được")
    max_score: float = Field(..., description="Thang điểm tối đa của bài thi (thường là 10)")
    percentage: float = Field(..., description="Tỷ lệ phần trăm làm đúng (0-100%)")

    passed: bool = Field(..., description="Trạng thái Đạt/Trượt dựa trên pass_score của Quiz")
    completion_time: datetime
    message: str

    overall_feedback: Optional[str] = Field(None, description="Lời nhận xét dựa trên điểm số")


class QuestionReviewOutput(BaseModel):
    """
    Chi tiết từng câu: User chọn gì? Đúng hay sai? Đáp án là gì?
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prompt: Dict[str, Any] = Field(..., description="Nội dung câu hỏi (đề bài)")
    
    # User response
    user_selected: Optional[Any] = Field(None, description="Đáp án user đã chọn (List ID hoặc Text)")
    is_correct: bool = Field(..., description="Trạng thái đúng/sai để tô màu UI")
    score_obtained: float = Field(..., description="Điểm đạt được của câu này")
    
    # Sensitive Data (Có thể null nếu Exam Mode không cho xem)
    correct_answer: Optional[Any] = Field(None, description="Đáp án đúng (chỉ hiện khi được phép)")
    explanation: Optional[str] = Field(None, description="Giải thích chi tiết (chỉ hiện khi được phép)")


class AttemptResultOutput(BaseModel):
    """
    Output cho màn hình Result Page.
    """
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    quiz_title: str
    status: str
    
    # Time info
    time_taken_seconds: int = Field(..., description="Tổng thời gian làm bài (giây)")
    time_submitted: Optional[datetime] = None
    
    # Score info
    score_obtained: float = Field(..., description="Tổng điểm đạt được")
    max_score: float = Field(..., description="Tổng điểm tối đa của đề")
    is_passed: bool = Field(..., description="Trạng thái Đạt/Trượt")
    
    correct_count: int = Field(..., description="Số câu làm đúng")
    total_questions: int = Field(..., description="Tổng số câu hỏi")

    # Detail list
    questions: List[QuestionReviewOutput] = Field(default_factory=list, description="Chi tiết từng câu hỏi")


# ==========================================
# Quiz Submit
# ==========================================

class QuizItemOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    mode: str  # 'exam' or 'practice'
    # Thông tin thời gian
    time_open: Optional[datetime]
    time_close: Optional[datetime]
    time_limit_str: Optional[str] # Convert duration to string
    
    # Trạng thái người dùng (Logic kiểu Moodle)
    user_status: str 
    best_score: Optional[float]
    attempts_count: int
    
    # Computed status của bài thi (Open/Closed)
    is_available: bool

# class QuizListOutput(BaseModel):
#     items: List[QuizItemDTO]
#     count: int
    