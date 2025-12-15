# domain/quiz_domain.py
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from django.utils import timezone
from uuid import UUID
from datetime import datetime
from typing import List

from quiz.models import Quiz 
from quiz.domains.exam_domain import ExamDomain



@dataclass
class AttemptHistoryItemDomain:
    """
    Value Object: Một dòng trong bảng lịch sử làm bài.
    """
    id: str         # ID để sau này click vào xem lại bài (Review)
    order: int      # Lần thứ mấy (1, 2, 3...)
    status: str     # 'completed', 'in_progress', 'overdue'
    score: Optional[float]
    time_submitted: Optional[datetime]
    
    @property
    def status_label(self) -> str:
        # Helper để hiển thị text đẹp cho frontend
        mapping = {
            'completed': 'Đã nộp',
            'in_progress': 'Đang làm',
            'overdue': 'Quá hạn'
        }
        return mapping.get(self.status, self.status)
    

@dataclass
class AccessDecisionDomain:
    is_allowed: bool = False
    action: str = "none"
    reason_message: str = ""
    button_label: str = "Không thể truy cập"
    ongoing_attempt_id: Optional[UUID] = None


@dataclass
class QuizPreflightDomain:
    """
    Domain Object chứa toàn bộ thông tin cần thiết cho màn hình Pre-flight.
    Không chứa logic HTTP, chỉ chứa data nghiệp vụ.
    """
    attempts_used: int
    score_best: float
    
    access_decision: AccessDecisionDomain # Nhúng object quyết định vào đây
    exam: ExamDomain
    history: List[AttemptHistoryItemDomain] = field(default_factory=list)
    
    def to_dict(self):
        return {
            "exam": self.exam.to_dict(),
            "access_decision": self.access_decision.__dict__,
            "stats": {
                "attempts_used": self.attempts_used,
                "score_best": self.score_best
            },
            # Serialize list history
            "history": [
                {
                    "id": item.id,
                    "order": item.order,
                    "status": item.status_label, # Dùng label hiển thị cho đẹp
                    "score": item.score,
                    "time_submitted": item.time_submitted
                } for item in self.history
            ]
        }