import uuid
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass



@dataclass
class QuestionSubmissionInput:
    """ DTO dùng chung cho việc Save Draft và Submit """
    answer_data: Dict[str, Any]

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)


class QuestionOptionOutput(BaseModel):
    id: str
    text: str

class QuestionContentOutput(BaseModel):
    """
    DTO trả về nội dung của MỘT câu hỏi cụ thể
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    prompt_text: str = Field(..., description="Nội dung câu hỏi")
    prompt_image: Optional[str] = None
    
    # Options này sẽ được shuffle ở tầng Domain hoặc Service trước khi đẩy vào đây
    options: List[QuestionOptionOutput] = []
    current_answer: Optional[dict]  # Chứa answer_data (ví dụ: {"selected_ids": [...]})
    is_flagged: bool


@dataclass
class QuestionSubmissionOutput:
    """ DTO Output trả về cho Client """
    question_id: uuid.UUID
    is_correct: bool
    score: float
    feedback: Optional[str]
    correct_answer_data: Optional[Dict[str, Any]]