from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from uuid import UUID



class BlockHeartbeatInput(BaseModel):
    # block_id: Optional[UUID]
    # Dữ liệu resume (JSON tuỳ ý)
    interaction_data: Dict[str, Any] = Field(default_factory=dict)
    # Dữ liệu quản lý (Optional - Frontend tính toán rồi gửi lên)
    is_completed: bool = False
    time_spent_add: int = 0 # Cộng dồn thời gian học (giây)


class BlockProgressBaseOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    block_id: UUID
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
    id: UUID # Cần ID để admin thực hiện thao tác sửa/xóa nếu cần
    user_id: Any # Cần biết tiến độ này của ai
    time_spent_seconds: int # Quan trọng để đánh giá mức độ chăm chỉ
    resume_data: Dict[str, Any] # Admin cũng cần xem user đang kẹt ở đâu


# --- 1. DTO (Data Transfer Object) ---
class BlockCompletionInput(BaseModel):
    block_id: UUID
    force_complete: bool = False


class CourseResumeBaseOutput(BaseModel):
    """
    Thông tin cốt lõi để điều hướng (Navigation)
    """
    model_config = ConfigDict(from_attributes=True)
    
    course_id: UUID
    module_id: UUID
    lesson_id: UUID
    block_id: UUID
    
    # Cờ quan trọng để Frontend hiển thị UI phù hợp
    # True: "Bắt đầu học" (Nút Start)
    # False: "Tiếp tục học" (Nút Resume)
    is_first_start: bool = False 
    is_completed: bool = False


# --- PUBLIC OUTPUT (Học viên) ---
# Focus: Navigation & Playback State
class CourseResumePublicOutput(CourseResumeBaseOutput):
    # User cần resume_data để player seek tới đúng giây (ví dụ: {"video_timestamp": 120})
    resume_data: Dict[str, Any] = Field(default_factory=dict)


# --- ADMIN OUTPUT (Giảng viên/Debug) ---
# Focus: Tracking & Audit
class CourseResumeAdminOutput(CourseResumeBaseOutput):
    user_id: Any # Admin cần biết đang check resume của ai
    # Admin cần biết user dừng lại lúc nào (ví dụ: dừng 3 ngày trước -> gửi noti nhắc)
    last_accessed: Optional[datetime] = None
    # Admin cũng cần xem data raw để debug nếu user báo lỗi "không resume được"
    resume_data: Dict[str, Any] = Field(default_factory=dict)



