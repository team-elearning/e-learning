from dataclasses import dataclass
from typing import Dict, Any
from quiz.models import Question 

@dataclass(frozen=True)
class QuestionDomain:
    """
    Đại diện cho domain "Câu hỏi" (Question).
    """
    id: str
    quiz_id: str
    position: int
    type: str
    prompt: Dict[str, Any]
    answer_payload: Dict[str, Any]
    hint: Dict[str, Any]

    @classmethod
    def from_model(cls, model: "Question") -> "QuestionDomain":
        """
        Tạo đối tượng QuestionDomain từ một instance model Question.
        """
        if not model:
            return None
        
        return cls(
            id=str(model.id),
            quiz_id=str(model.quiz_id), # Lưu ID của quiz cha
            position=model.position,
            type=model.type,
            prompt=model.prompt or {},
            answer_payload=model.answer_payload or {},
            hint=model.hint or {}
        )
    
    def to_dict(self) -> dict:
        """ Chuyển đổi sang dạng dict (JSON-serializable). """
        return self.__dict__