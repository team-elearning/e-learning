import uuid
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass



class QuestionSubmissionInput(BaseModel):
    """ DTO dùng chung cho việc Save Draft và Submit """
    answer_data: Dict[str, Any]
    question_type: str
    
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
    
    # [FIX] Trả về cấu trúc Rich Prompt
    prompt: Dict[str, Any]
    
    current_answer: Optional[dict]  # Chứa answer_data (ví dụ: {"selected_ids": [...]})
    is_flagged: bool
    submission_result: Optional[Dict[str, Any]] = None


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
    question_type: str
    options: List[Dict[str, Any]] = []

    # === Câu trả lời của User ===
    # Quan trọng: FE cần cái này để tô màu những gì user đã chọn
    user_answer_data: Dict[str, Any] # Raw JSON (để logic tô màu/check lại nếu cần)
    user_answer_text: str

    correct_answer_data: Optional[Dict[str, Any]] = None
    correct_answer_text: Optional[str] = None

    # === Kết quả chấm ===
    score: float
    max_score: float            # <--- Mới thêm: Để biết điểm trần (VD: 1.0 hay 5.0)
    is_correct: bool
    
    # === Phản hồi hệ thống ===
    feedback: Optional[str] = None
    