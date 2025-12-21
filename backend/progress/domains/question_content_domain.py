import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

from progress.models import QuizAttempt



@dataclass
class QuestionContentDomain:
    id: uuid.UUID
    type: str

    # [FIX] Thay vì prompt_text/image, trả về nguyên object prompt đã xử lý
    # Để Frontend render thống nhất (Rich Text + Media + Options)
    prompt: Dict[str, Any]

    current_answer: dict  # Chứa answer_data (ví dụ: {"selected_ids": [...]})
    is_flagged: bool # Trạng thái cắm cờ
    submission_result: Optional[dict]