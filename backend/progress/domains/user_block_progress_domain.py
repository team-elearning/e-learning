from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID



@dataclass
class UserBlockProgressDomain:
    id: UUID
    user_id: UUID  
    block_id: UUID
    is_completed: bool
    time_spent_seconds: int
    resume_data: Dict[str, Any]
    last_accessed: datetime
    score: Optional[float] = None

    @classmethod
    def from_model(cls, model_instance) -> 'UserBlockProgressDomain':
        """
        Factory method: Chuyển đổi từ Django Model -> Domain Entity.
        """
        return cls(
            id=model_instance.id,
            # Lưu ý: Dùng user_id và block_id (có _id) để tránh query thêm DB 
            # nếu object user/block chưa được prefetch.
            user_id=model_instance.user_id, 
            block_id=model_instance.block_id,
            is_completed=model_instance.is_completed,
            time_spent_seconds=model_instance.time_spent_seconds,
            score=model_instance.score,
            # Đảm bảo resume_data luôn là dict kể cả khi DB lưu null (safety)
            resume_data=model_instance.resume_data if model_instance.resume_data else {},
            last_accessed=model_instance.last_accessed
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Chuyển đổi Domain Entity -> Dictionary (thường dùng để trả về API).
        Xử lý serialize UUID và Datetime sang string cho an toàn với JSON.
        """
        return {
            "id": str(self.id),
            "user_id": self.user_id, # Nếu user_id là UUID thì nên wrap str()
            "block_id": str(self.block_id),
            "is_completed": self.is_completed,
            "time_spent_seconds": self.time_spent_seconds,
            "score": self.score,
            "resume_data": self.resume_data,
            # Format ISO 8601 cho frontend dễ parse
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }

    # --- BUSINESS LOGIC (Optional) ---
    # Bạn có thể thêm các hàm nghiệp vụ ngay tại đây thay vì để rải rác
    
    def update_progress(self, new_data: dict, time_add: int = 0):
        """Logic update dữ liệu resume và cộng dồn thời gian"""
        self.resume_data.update(new_data)
        self.time_spent_seconds += time_add
        # Update last_accessed cần xử lý ở service hoặc lúc save
    
    def mark_as_completed(self):
        """Logic hoàn thành bài học"""
        self.is_completed = True
