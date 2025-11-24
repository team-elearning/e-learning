from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List



@dataclass
class QuizAttemptDomain:
    """Entity: Đại diện cho 1 lần làm bài"""
    id: UUID
    quiz_id: UUID
    user_id: int
    status: str
    time_start: datetime
    current_question_index: int
    
    @classmethod
    def from_model(cls, model):
        return cls(
            id=model.id,
            quiz_id=model.quiz_id,
            user_id=model.user_id,
            status=model.status,
            time_start=model.time_start,
            current_question_index=model.current_question_index
        )


@dataclass
class AttemptCreationResultDomain:
    """
    Aggregate: Kết quả của hành động 'Bắt đầu làm bài'.
    Gói gọn cả Object Attempt và Metadata hành động.
    """
    attempt: QuizAttemptDomain
    action: str  # 'created' | 'resumed'
    detail: str  # Message thông báo


@dataclass
class QuestionTakingDomain:
    """
    Entity: Một câu hỏi trong giao diện làm bài.
    Bao gồm: Nội dung câu hỏi + Trạng thái trả lời của user (nếu có).
    Moodle gọi đây là 'Slot' (kết hợp Question + Response).
    """
    id: UUID
    type: str
    prompt: Dict[str, Any] # Nội dung câu hỏi (Text, Ảnh)
    
    # State của User (Resume)
    current_selection: Optional[Dict[str, Any]] = None # User đã chọn gì?
    is_answered: bool = False # Đã làm chưa? (Dùng để tô màu xanh/trắng navigation)

    is_flagged: bool = False
    
    # Bảo mật: Tuyệt đối KHÔNG có answer_payload ở đây


@dataclass
class AttemptTakingDomain:
    """
    Aggregate Root: Toàn bộ ngữ cảnh màn hình làm bài.
    """
    attempt_id: UUID
    quiz_title: str
    
    # Time
    time_remaining_seconds: Optional[int]
    
    # Navigation
    current_question_index: int
    total_questions: int
    
    # Content
    questions: List[QuestionTakingDomain]


@dataclass
class SaveAnswerResultDomain:
    """
    Domain Entity: Kết quả của hành động lưu bài.
    Service sẽ trả về cái này.
    """
    status: str
    saved_at: datetime


@dataclass
class SubmitAttemptResultDomain:
    attempt_id: UUID
    status: str          # 'completed'
    score_obtained: float
    passed: bool         # True/False dựa trên pass_score
    completion_time: datetime
    message: str         # "Nộp bài thành công"


@dataclass
class QuestionReviewDomain:
    """
    Chi tiết kết quả của 1 câu hỏi.
    """
    id: UUID
    prompt: Dict[str, Any]      # Nội dung câu hỏi
    user_selected: Any          # Đáp án user chọn (List ID hoặc Text)
    is_correct: bool            # Đúng hay sai?
    score_obtained: float       # Điểm đạt được câu này
    
    # Các field nhạy cảm (Chỉ hiện khi Practice Mode hoặc Config cho phép)
    correct_answer: Optional[Any] = None  # Đáp án đúng là gì?
    explanation: Optional[str] = None     # Giải thích chi tiết


@dataclass
class AttemptResultDomain:
    """
    Tổng quan kết quả bài thi.
    """
    attempt_id: UUID
    quiz_title: str
    status: str
    time_taken_seconds: int     # Thời gian làm bài
    time_submitted: datetime
    
    # Điểm số
    score_obtained: float       # Điểm thô
    max_score: float            # Tổng điểm của đề
    is_passed: bool             # Đạt/Trượt
    
    # Danh sách chi tiết (Có thể rỗng nếu mode Exam không cho xem lại bài)
    questions: List[QuestionReviewDomain] = field(default_factory=list)