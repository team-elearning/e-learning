from dataclasses import dataclass
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