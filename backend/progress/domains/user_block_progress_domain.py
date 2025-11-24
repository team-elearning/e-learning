from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID



@dataclass
class UserBlockProgressDomain:
    id: Optional[UUID]  # None nếu chưa lưu DB
    user_id: UUID   
    block_id: UUID
    
    # --- Trạng thái học tập ---
    status: str  # Thay vì bool is_completed, dùng Enum: 'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED'
    time_spent_seconds: int
    resume_data: Dict[str, Any]
    last_accessed: Optional[datetime]
    score: Optional[float] = None
    
    # --- MỞ RỘNG: Metadata từ ContentBlock (Để Frontend hiển thị) ---
    # Giúp FE biết tổng thời lượng để vẽ thanh loading mà không cần gọi API khác
    block_total_duration: Optional[int] = None 
    block_passing_score: Optional[float] = None
    
    # --- Calculated Field ---
    progress_percentage: float = 0.0 

    @classmethod
    def from_model(cls, progress_model, content_block) -> 'UserBlockProgressDomain':
        """
        Factory method kết hợp dữ liệu từ Progress (User) và ContentBlock (System).
        """
        # Logic tính status & percentage
        status = 'IN_PROGRESS'
        if progress_model.is_completed:
            status = 'COMPLETED'
        
        # Tính phần trăm (Ví dụ đơn giản)
        percent = 0.0
        if content_block.duration_seconds and content_block.duration_seconds > 0:
            percent = min(100.0, (progress_model.time_spent_seconds / content_block.duration_seconds) * 100)
            
        return cls(
            id=progress_model.id,
            user_id=progress_model.user_id,
            block_id=progress_model.block_id,
            status=status, # Mới
            time_spent_seconds=progress_model.time_spent_seconds,
            resume_data=progress_model.resume_data or {},
            last_accessed=progress_model.last_accessed,
            score=progress_model.score,
            
            # Map dữ liệu từ Block sang
            block_total_duration=content_block.duration_seconds, # Giả sử model Block có trường này
            block_passing_score=content_block.passing_score,
            progress_percentage=round(percent, 2)
        )
    
    @classmethod
    def create_transient(cls, user, block) -> 'UserBlockProgressDomain':
        """Tạo object rỗng cho người chưa học bao giờ"""
        return cls(
            id=None,
            user_id=user.id,
            block_id=block.id,
            status='NOT_STARTED',
            time_spent_seconds=0,
            resume_data={},
            last_accessed=None,
            score=None,
            block_total_duration=block.duration_seconds,
            block_passing_score=block.passing_score,
            progress_percentage=0.0
        )
