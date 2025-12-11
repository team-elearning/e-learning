from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
import uuid



class QuestionInput(BaseModel):
    """
    DTO dùng cho Input (Create/Update).
    Tất cả các trường đều phải là Optional hoặc có Default để hỗ trợ:
    1. Tạo Skeleton (Không gửi gì cả).
    2. Partial Update (Chỉ gửi những trường cần sửa).
    """
    id: Optional[uuid.UUID] = None 
    
    # Sửa: Thêm '= None' để cho phép FE không gửi trường 'type'
    type: Optional[str] = None 
    
    # Sửa: Thay 'Field(...)' bằng 'default_factory=dict'
    # Nghĩa là: Nếu FE không gửi, thì giá trị mặc định là {}
    prompt: Dict[str, Any] = Field(default_factory=dict, description="Nội dung câu hỏi")
    
    # Sửa: Tương tự prompt
    answer_payload: Dict[str, Any] = Field(default_factory=dict, description="Đáp án đúng")
    
    hint: Dict[str, Any] = Field(default_factory=dict)


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


class QuestionInstructorOutput(QuestionPublicOutput):
    """
    DTO Output dành cho Giáo viên/Admin.
    Hiện đầy đủ đáp án và gợi ý.
    """
    model_config = ConfigDict(from_attributes=True)

    answer_payload: Dict[str, Any] # Giáo viên cần xem đáp án cấu hình
    hint: Dict[str, Any]


class QuestionAdminOutput(QuestionPublicOutput):
    """
    DTO Output dành cho Giáo viên/Admin.
    Hiện đầy đủ đáp án và gợi ý.
    """
    model_config = ConfigDict(from_attributes=True)
    
    owner_id: Optional[uuid.UUID]
    owner_name: Optional[str]
    answer_payload: Dict[str, Any] # Giáo viên cần xem đáp án cấu hình
    hint: Dict[str, Any]