import uuid
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass



class QuestionSubmissionInput(BaseModel):
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


class QuizItemResultOutput(BaseModel):
    """ 
    DTO Output trả về cho Client.
    Dùng chung cho:
    1. Response của API Submit từng câu (POST .../submit)
    2. Item trong danh sách chi tiết của API Finish/History
    """
    model_config = ConfigDict(from_attributes=True)

    # === Thông tin câu hỏi ===
    question_id: uuid.UUID
    question_text: str          # <--- Mới thêm: Để FE hiển thị lại đề bài nếu cần
    
    # === Câu trả lời của User ===
    # Quan trọng: FE cần cái này để tô màu những gì user đã chọn
    user_answer: Dict[str, Any] 
    correct_answer: Optional[Dict[str, Any]] = None

    # === Kết quả chấm ===
    score: float
    max_score: float            # <--- Mới thêm: Để biết điểm trần (VD: 1.0 hay 5.0)
    is_correct: bool
    
    # === Phản hồi hệ thống ===
    feedback: Optional[str] = None
    