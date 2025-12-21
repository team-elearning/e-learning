from uuid import UUID
from dataclasses import dataclass
from typing import Optional, Dict, List

from progress.models import QuizAttempt, QuestionAnswer
from quiz.models import Question



@dataclass
class QuizItemResultDomain:
    """Kết quả chi tiết của 1 câu hỏi"""
    question_id: UUID
    question_text: str       # Text câu hỏi (để hiển thị review)
    question_type: str

    # Context hiển thị options (để render lại đề bài)
    options: List[dict]

    user_answer_data: dict # Raw data lưu trong DB
    user_answer_text: str # Text hiển thị (VD: "Hồ Chí Minh") -> FE đỡ phải map lại

    correct_answer_data: Optional[dict] # Raw data đáp án đúng (Ẩn nếu mode exam chưa công bố)
    correct_answer_text: Optional[str]  # Text hiển thị (VD: "Hà Nội")

    score: float             # Điểm đạt được
    max_score: float         # Điểm tối đa của câu
    is_correct: bool
    feedback: Optional[dict] = None            # Lời giải thích


    @staticmethod
    def _format_text(q_type: str, data: dict, lookup: dict) -> str:
        """Helper map ID -> Text siêu gọn"""
        if not data: return "Chưa trả lời"

        if q_type == 'multiple_choice_single':
            # Data format: {'selected_id': 'A'} hoặc Correct: {'correct_id': 'A'}
            key = data.get('selected_id') or data.get('correct_id')
            return lookup.get(key, str(key))
            
        elif q_type == 'multiple_choice_multi':
            # Data: {'selected_ids': ['A', 'B']}
            vals = data.get('selected_ids') or data.get('correct_ids') or []
            return ", ".join([lookup.get(str(v), str(v)) for v in vals])
            
        elif q_type == 'true_false':
            val = data.get('selected_value')
            if val is None: val = data.get('correct_value')
            return "Đúng" if val is True else "Sai" if val is False else ""

        elif q_type == 'matching':
            matches = data.get('matches', {})
            # Format: A->1, B->2. (Cần map cả 2 vế nếu prompt phức tạp, ở đây map vế phải)
            pairs = [f"{k} -> {lookup.get(str(v), v)}" for k, v in matches.items()]
            return "; ".join(pairs)

        return str(data.get('text') or data) # Short Answer / Essay


    @classmethod
    def from_model(cls, ans: "QuestionAnswer", lookup_map: dict = None) -> "QuizItemResultDomain":
        """
        Map từ Model QuestionAnswer sang Domain.
        :param ans: Object QuestionAnswer (kèm question đã select_related nếu có)
        :param show_correct_answer: Flag từ Service truyền vào (dựa trên mode Exam/Practice)
        """
        from progress.services.question_attempt_service import get_correct_answer_for_display

        # Phòng hờ trường hợp question bị xóa hoặc chưa fetch
        question = ans.question
        prompt = question.prompt or {}

        # Fallback nếu service quên truyền map (Safety)
        if lookup_map is None:
            opts = question.prompt.get('options', [])
            lookup_map = {o['id']: o['text'] for o in opts}

        user_text = cls._format_text(question.type, ans.answer_data, lookup_map)

        # 2. Format Correct Answer (Lấy từ payload)
        # Lưu ý: Ẩn hiện correct answer đã được xử lý ở View/Serializer rồi,
        # Domain cứ map hết, việc ẩn là việc của tầng Presentation.
        correct_payload = question.answer_payload or {}
        correct_text = cls._format_text(question.type, correct_payload, lookup_map)

        return cls(
            question_id=ans.question_id,
            question_text=prompt.get('content') or prompt.get('text', ''),
            question_type=question.type,
            options=prompt.get('options', []),

            user_answer_data=ans.answer_data,
            user_answer_text=user_text,

            correct_answer_data=correct_payload,
            correct_answer_text=correct_text,

            score=ans.score,
            max_score=getattr(question, 'score', 1.0),
            is_correct=ans.is_correct,
            feedback=ans.feedback,
        )