import uuid
from dataclasses import dataclass
from typing import Optional, Dict



@dataclass
class QuestionSubmissionDomain:
    question_id: uuid.UUID
    is_correct: bool
    score: float
    feedback: Optional[str] = None
    correct_answer_data: Optional[Dict] = None