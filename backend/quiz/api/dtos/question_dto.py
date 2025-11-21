from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
import uuid



class QuestionInput(BaseModel):
    """
    DTO dùng cho Input (Create/Update) nằm lồng trong Exam.
    """
    id: Optional[uuid.UUID] = None # Có ID -> Update, Không -> Create
    type: str
    prompt: Dict[str, Any] = Field(..., description="Nội dung câu hỏi (text, images, options)")
    answer_payload: Dict[str, Any] = Field(..., description="Đáp án đúng (correct_ids)")
    hint: Dict[str, Any] = Field(default_factory=dict)
    position: int = 0

class QuestionPublicOutput(BaseModel):
    """
    DTO Output dành cho Học viên/Public.
    QUAN TRỌNG: Tuyệt đối KHÔNG trả về 'answer_payload' (đáp án đúng).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    prompt: Dict[str, Any] # Học viên chỉ cần đề bài và các options (A,B,C,D)
    position: int
    # score: float -> Có thể hiện hoặc ẩn tùy logic

class QuestionAdminOutput(QuestionPublicOutput):
    """
    DTO Output dành cho Giáo viên/Admin.
    Hiện đầy đủ đáp án và gợi ý.
    """
    answer_payload: Dict[str, Any] # Giáo viên cần xem đáp án cấu hình
    hint: Dict[str, Any]