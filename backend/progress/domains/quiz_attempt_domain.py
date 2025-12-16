from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from django.utils import timezone

from progress.models import QuizAttempt



@dataclass
class QuizAttemptDomain:
    """Entity: Đại diện cho 1 lần làm bài"""
    id: UUID
    quiz_title: str
    time_limit_seconds: Optional[int]
    time_start: datetime
    questions_order: List[str]
    current_index: int
    user_id: int
    status: str
    
    @classmethod
    def from_model(cls, attempt: "QuizAttempt"):
        # Tính toán time limit (nếu cần xử lý logic bù giờ)
        limit_sec = int(attempt.quiz.time_limit.total_seconds()) if attempt.quiz.time_limit else None
        
        return cls(
            id=attempt.id,
            quiz_title=attempt.quiz.title,
            time_limit_seconds=limit_sec,
            time_start=attempt.time_start,
            questions_order=attempt.questions_order,
            current_index=attempt.current_question_index,
            status=attempt.status,
        )