from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import Any, Dict
from typing import Dict, Any, Optional
from datetime import datetime



class BlockHeartbeatInput(BaseModel):
    block_id: UUID4
    # Dữ liệu resume (JSON tuỳ ý)
    resume_data: Dict[str, Any] = Field(default_factory=dict)
    # Dữ liệu quản lý (Optional - Frontend tính toán rồi gửi lên)
    is_completed: bool = False
    time_spent_add: int = 0 # Cộng dồn thời gian học (giây)


class BlockProgressBaseOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    block_id: UUID4
    is_completed: bool
    score: Optional[float] = None
    last_accessed: Optional[datetime] = None


class BlockProgressPublicOutput(BlockProgressBaseOutput):
    resume_data: Dict[str, Any] = Field(default_factory=dict)
    # Học viên không cần biết "time_spent_seconds" chính xác từng giây, 
    # hoặc nếu cần hiển thị dạng "15 phút" thì frontend tự tính từ logs sau.


# --- ADMIN OUTPUT (Cho Giảng Viên/Hệ thống) ---
# Focus: Analytics, Grading, Debugging
class BlockProgressAdminOutput(BlockProgressBaseOutput):
    id: UUID4 # Cần ID để admin thực hiện thao tác sửa/xóa nếu cần
    user_id: Any # Cần biết tiến độ này của ai
    time_spent_seconds: int # Quan trọng để đánh giá mức độ chăm chỉ
    resume_data: Dict[str, Any] # Admin cũng cần xem user đang kẹt ở đâu




