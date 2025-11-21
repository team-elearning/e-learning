# domains/question_domain.py
import uuid
from typing import Dict, Any

class QuestionDomain:
    def __init__(self, id: uuid.UUID, type: str, prompt: Dict, answer_payload: Dict, position: int, hint: Dict = None):
        self.id = id
        self.type = type
        self.prompt = prompt
        self.answer_payload = answer_payload
        self.position = position
        self.hint = hint or {}

    def to_dict(self):
        return {
            "id": str(self.id),
            "type": self.type,
            "prompt": self.prompt,
            "answer_payload": self.answer_payload,
            "position": self.position,
            "hint": self.hint
        }

    @classmethod
    def from_model(cls, model):
        return cls(
            id=model.id,
            type=model.type,
            prompt=model.prompt,
            answer_payload=model.answer_payload,
            position=model.position,
            hint=model.hint
        )