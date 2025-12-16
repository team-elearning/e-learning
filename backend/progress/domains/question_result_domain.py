from uuid import UUID
from dataclasses import dataclass
from typing import Optional, Dict

from progress.models import QuizAttempt, QuestionAnswer



@dataclass
class QuizItemResultDomain:
    """Kết quả chi tiết của 1 câu hỏi"""
    question_id: UUID
    question_text: str       # Text câu hỏi (để hiển thị review)
    user_answer: dict        # Câu trả lời của user
    score: float             # Điểm đạt được
    max_score: float         # Điểm tối đa của câu
    is_correct: bool
    correct_answer: Optional[dict] = None     # Đáp án đúng (để so sánh)
    feedback: Optional[dict] = None            # Lời giải thích


    @classmethod
    def from_model(cls, ans: "QuestionAnswer", show_correct_answer: bool = False) -> "QuizItemResultDomain":
        """
        Map từ Model QuestionAnswer sang Domain.
        :param ans: Object QuestionAnswer (kèm question đã select_related nếu có)
        :param show_correct_answer: Flag từ Service truyền vào (dựa trên mode Exam/Practice)
        """
        from progress.services.question_attempt_service import get_correct_answer_for_display

        # Phòng hờ trường hợp question bị xóa hoặc chưa fetch
        q_obj = ans.question
        
        # Lấy payload đáp án đúng (chỉ lấy khi được phép)
        correct_payload = None
        if show_correct_answer and q_obj:
            correct_payload = get_correct_answer_for_display(q_obj)

        return cls(
            question_id=ans.question_id,
            question_text=q_obj.prompt.get('text', '') if (q_obj and q_obj.prompt) else "Câu hỏi",
            
            user_answer=ans.answer_data,
            score=ans.score,
            max_score=getattr(q_obj, 'score', 1.0) if q_obj else 1.0,
            
            is_correct=ans.is_correct,
            feedback=ans.feedback,
            
            correct_answer=correct_payload
        )