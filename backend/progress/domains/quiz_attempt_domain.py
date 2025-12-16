from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from django.utils import timezone

from progress.models import QuizAttempt, QuestionAnswer



@dataclass
class QuizItemResultDomain:
    """Kết quả chi tiết của 1 câu hỏi"""
    question_id: UUID
    question_text: str       # Text câu hỏi (để hiển thị review)
    user_answer: dict        # Câu trả lời của user
    correct_answer: Optional[dict]     # Đáp án đúng (để so sánh)
    score: float             # Điểm đạt được
    max_score: float         # Điểm tối đa của câu
    is_correct: bool
    feedback: str            # Lời giải thích

    @classmethod
    def from_model(cls, ans: "QuestionAnswer") -> "QuizItemResultDomain":
        # Helper map từ Model Answer -> Domain Item
        return cls(
            question_id=ans.question_id,
            question_text=ans.question.content if ans.question else "Câu hỏi đã bị xóa", # Cần field content
            user_answer=ans.answer_data,
            # Chỉ trả về đáp án đúng nếu logic cho phép (VD: bài thi đã đóng)
            correct_answer=ans.question.get_correct_answer_payload() if ans.question else None,
            score=ans.score,
            max_score=getattr(ans.question, 'score', 1.0),
            is_correct=ans.is_correct,
            feedback=ans.feedback
        )


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
    def from_model(cls, attempt: "QuizAttempt") -> "QuizAttemptDomain":
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

        domain_items = []
        # Kiểm tra xem Service có "kẹp" sẵn dữ liệu vào biến tạm _cached_answers không?
        source_answers = getattr(attempt, '_cached_answers', None)

        if source_answers is None:
            # Fallback: Nếu không có cache (VD: gọi từ chỗ khác), buộc phải query DB
            # Dùng select_related để tránh N+1 khi truy cập question.content
            # Lưu ý: Lúc này thứ tự có thể không đúng theo questions_order nếu không sort lại
            source_answers = attempt.answers.select_related('question').all()

        for ans in source_answers:
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
            is_finished=(attempt.status == 'completed'), # Hoặc check trong STATUS_CHOICES
        
            items=domain_items
        )