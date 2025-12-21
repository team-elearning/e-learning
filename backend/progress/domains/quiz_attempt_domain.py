from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from django.utils import timezone

from progress.models import QuizAttempt
from progress.domains.question_result_domain import QuizItemResultDomain



@dataclass
class QuizAttemptDomain:
    """Entity: Đại diện cho 1 lần làm bài"""
    id: UUID
    quiz_title: str
    quiz_id: UUID  # Nên có ID của quiz gốc
    user_id: UUID

    # --- Time & Context ---
    time_start: datetime
    completed_at: datetime
    time_limit_seconds: Optional[int]
    time_taken_seconds: Optional[int]
    
    # --- Progress ---
    questions_order: List[str]
    current_index: int
    status: str

    # --- Results ---
    score: float
    max_score: float
    is_passed: bool

    percentage: float                    
    is_finished: bool

    items: List[QuizItemResultDomain]
    
    @classmethod
    def from_model(cls, attempt: "QuizAttempt", items: List[QuizItemResultDomain] = None) -> "QuizAttemptDomain":
        # 1. Xử lý Time Limit (Config từ Quiz gốc)
        limit_sec = None
        if attempt.quiz and attempt.quiz.time_limit:
            limit_sec = int(attempt.quiz.time_limit.total_seconds())

        # 2. Xử lý Time Taken (Thời gian thực tế đã làm)
        # Model lưu time_submitted, nhưng Domain cần số giây cụ thể (duration)
        duration_sec = 0
        if attempt.time_submitted and attempt.time_start:
            delta = attempt.time_submitted - attempt.time_start
            duration_sec = int(delta.total_seconds())
        elif attempt.status == 'in_progress':
             # Tùy logic: có thể tính thời gian từ start đến hiện tại (live duration)
             # Ở đây mình để None hoặc 0
             duration_sec = int((datetime.now(attempt.time_start.tzinfo) - attempt.time_start).total_seconds())

        # 3. Tính phần trăm điểm (Avoid division by zero)
        calc_percentage = 0.0
        if attempt.max_score > 0:
            calc_percentage = (attempt.score / attempt.max_score) * 100

        # 4. Xử lý Items (Logic ưu tiên: Tham số truyền vào > Cached property > Query DB)
        domain_items = items  # Ưu tiên 1: Lấy từ tham số

        if domain_items is None:
            # Ưu tiên 2: Lấy từ cache
            source_answers = getattr(attempt, '_cached_graded_answers', getattr(attempt, '_cached_answers', None))
            
            if source_answers:
                 domain_items = [QuizItemResultDomain.from_model(ans) for ans in source_answers]
            else:
                 # Chiến lược Fail-Fast hoặc Lazy Load có kiểm soát
                 # Ở các hệ thống lớn, họ thường log warning ở đây vì điều này chứng tỏ Service chưa làm tròn trách nhiệm pre-load.
                 # Tuy nhiên để an toàn cho App hiện tại, ta giữ fallback query nhưng tối ưu nhất có thể.
               
                 source_answers = attempt.answers.select_related('question').order_by('question_id') # Query nhẹ nhất có thể
                 ans_map = {a.question_id: a for a in source_answers}
                 
                 # Re-order in Python (CPU bound > IO bound)
                 domain_items = []
                 for qid in attempt.questions_order:
                     ans = ans_map.get(UUID(qid))
                     if ans:
                         domain_items.append(QuizItemResultDomain.from_model(ans))

        # 4. Map dữ liệu
        return cls(
            id=attempt.id,
            quiz_title=attempt.quiz.title if attempt.quiz else "Unknown Quiz",
            quiz_id=attempt.quiz_id, # Django automatically adds _id field
            user_id=attempt.user_id, # Django automatically adds _id field
            
            time_start=attempt.time_start,
            completed_at=attempt.time_submitted, # Map field name: time_submitted -> completed_at
            time_limit_seconds=limit_sec,
            time_taken_seconds=duration_sec,
            
            questions_order=attempt.questions_order,
            current_index=attempt.current_question_index,
            status=attempt.status,
            
            score=attempt.score,
            max_score=attempt.max_score,
            is_passed=attempt.is_passed,
            
            # Virtual fields
            percentage=round(calc_percentage, 2),
            is_finished=(attempt.status == 'submitted'), # Hoặc check trong STATUS_CHOICES
        
            items=domain_items
        )