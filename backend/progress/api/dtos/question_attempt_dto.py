import uuid
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, Dict, Any, List
from datetime import datetime



# --- DTO 2: Nội dung chi tiết từng câu hỏi (Load từng câu) ---
class QuestionOptionDTO(BaseModel):
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
    options: List[QuestionOptionDTO] = []
    current_answer: Optional[dict]  # Chứa answer_data (ví dụ: {"selected_ids": [...]})
    is_flagged: bool