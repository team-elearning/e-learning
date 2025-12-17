from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID



@dataclass
class UserBlockProgressDomain:
    id: Optional[UUID]  # None nếu chưa lưu DB
    user_id: UUID   
    block_id: UUID
    enrollment_id: Optional[UUID]
    
    # --- Trạng thái học tập ---
    status: str  # Thay vì bool is_completed, dùng Enum: 'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED'
    is_completed: bool
    completed_at: Optional[datetime]

    time_spent_seconds: int
    interaction_data: Dict[str, Any]
    last_accessed: Optional[datetime]
    
    block_type: str             # 'video', 'quiz', 'pdf'...
    total_duration: int = 0     # Thời lượng tổng của video (giây)
    progress_percentage: float = 0.0

    @classmethod
    def from_model(cls, progress_model, content_block) -> 'UserBlockProgressDomain':
        """
        Factory Method: Merge dữ liệu từ Model Progress (User) và Model Block (System).
        """
        # 1. Tính toán Status
        status = 'IN_PROGRESS'
        if progress_model.is_completed:
            status = 'COMPLETED'
        elif progress_model.time_spent_seconds == 0 and not progress_model.interaction_data:
            status = 'NOT_STARTED'

        # 2. Lấy Metadata từ Block (Payload thường lưu duration video)
        duration = content_block.duration
        
        # 3. Tính % tiến độ (Chỉ tính cho Video/Audio, Text thì là 0 hoặc 100)
        percent = 0.0
        if progress_model.is_completed:
            percent = 100.0
        elif duration > 0:
            percent = min(100.0, (progress_model.time_spent_seconds / duration) * 100)
        
        return cls(
            id=progress_model.id,
            user_id=progress_model.user_id,
            block_id=progress_model.block_id,
            enrollment_id=progress_model.enrollment_id,
            
            status=status,
            is_completed=progress_model.is_completed,
            completed_at=progress_model.completed_at,
            
            time_spent_seconds=progress_model.time_spent_seconds,
            interaction_data=progress_model.interaction_data or {},
            last_accessed=progress_model.last_accessed,
            
            block_type=content_block.type,
            total_duration=duration,
            progress_percentage=round(percent, 2)
        )
    
    @classmethod
    def create_transient(cls, user, block) -> 'UserBlockProgressDomain':
        """
        Tạo object rỗng cho người chưa học bao giờ (chưa có record trong DB).
        """
        return cls(
            id=None,
            user_id=user.id,
            block_id=block.id,
            enrollment_id=None, # Chưa có record nên chưa cần link enrollment ngay
            
            status='NOT_STARTED',
            is_completed=False,     # SỬA 3: Bổ sung field thiếu
            completed_at=None,      # SỬA 3: Bổ sung field thiếu
            
            time_spent_seconds=0,
            interaction_data={},
            last_accessed=None,
            
            block_type=block.type,  # SỬA 3: Bổ sung field thiếu
            total_duration=block.duration, # Lấy từ model ContentBlock
            progress_percentage=0.0
        )
