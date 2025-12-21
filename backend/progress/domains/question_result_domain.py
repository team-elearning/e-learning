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
    def _get_display_text(q_type: str, data: dict, option_map: dict) -> str:
        """Helper chuyển raw data thành text hiển thị"""
        if not data: return "Chưa trả lời"

        if q_type == 'multiple_choice_single':
            # Data format: {'selected_id': 'A'} hoặc Correct: {'correct_id': 'A'}
            key = data.get('selected_id') or data.get('correct_id')
            return option_map.get(key, str(key))
            
        elif q_type == 'multiple_choice_multi':
            # Data: {'selected_ids': ['A', 'B']}
            keys = data.get('selected_ids') or data.get('correct_ids') or []
            texts = [option_map.get(k, str(k)) for k in keys]
            return ", ".join(texts)
            
        elif q_type == 'true_false':
            val = data.get('selected_value')
            if val is None: val = data.get('correct_value')
            return "Đúng" if val is True else "Sai" if val is False else ""

        # Các loại khác (Short answer, essay...) thì data thường là text sẵn
        return str(data)


    @classmethod
    def from_model(cls, ans: "QuestionAnswer", question_obj: "Question" = None, show_correct_answer: bool = False) -> "QuizItemResultDomain":
        """
        Map từ Model QuestionAnswer sang Domain.
        :param ans: Object QuestionAnswer (kèm question đã select_related nếu có)
        :param show_correct_answer: Flag từ Service truyền vào (dựa trên mode Exam/Practice)
        """
        from progress.services.question_attempt_service import get_correct_answer_for_display

        # Phòng hờ trường hợp question bị xóa hoặc chưa fetch
        q = question_obj or ans.question

        prompt_data = getattr(q, 'prompt', {}) or {}
        options = prompt_data.get('options', [])
        option_map = {opt['id']: opt['text'] for opt in options if 'id' in opt and 'text' in opt}

        user_text = cls._get_display_text(q.type, ans.answer_data, option_map)

        correct_data = getattr(q, 'answer_payload', {})
        correct_text = cls._get_display_text(q.type, correct_data, option_map)

        return cls(
            question_id=ans.question_id,
            question_text=q.prompt.get('text', ''),
            question_type=q.type,
            options=options,

            user_answer=ans.answer_data,
            user_answer_text=user_text,

            correct_answer_data=ans.answer_data,
            correct_answer_text=correct_text,

            score=ans.score,
            max_score=getattr(q, 'score', 1.0),
            is_correct=ans.is_correct,
            feedback=ans.feedback,
        )