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