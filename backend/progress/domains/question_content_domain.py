import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

from progress.models import QuizAttempt



@dataclass
class QuestionContentDomain:
    id: uuid.UUID
    type: str
    prompt_text: str
    prompt_image: Optional[str]
    options: List[dict] # List option đã được shuffle
    current_answer: dict  # Chứa answer_data (ví dụ: {"selected_ids": [...]})
    is_flagged: bool # Trạng thái cắm cờ
    submission_result: Optional[dict]