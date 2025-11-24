from dataclasses import dataclass
from typing import Optional, Dict, Any
import uuid
from datetime import datetime



@dataclass
class ResumePositionDomain:
    """
    Domain Object đại diện cho vị trí user cần học tiếp.
    Không phụ thuộc vào Django Model.
    """
    block_id: uuid.UUID
    lesson_id: uuid.UUID
    module_id: uuid.UUID
    course_id: uuid.UUID

    resume_data: Dict[str, Any]
    is_completed: bool

    user_id: Any

    is_first_start: bool = False # True nếu user chưa học gì cả (bắt đầu từ đầu)
    last_accessed: Optional[datetime] = None

    course_progress_percent: float = 0.0  # Ví dụ: 45.5%
    total_blocks: int = 0                 # Tổng số bài
    completed_blocks: int = 0             # Số bài đã xong

    def to_dict(self):
        """Convert domain -> dict JSON-friendly"""
        return {
            "block_id": str(self.block_id),
            "lesson_id": str(self.lesson_id),
            "module_id": str(self.module_id),
            "course_id": str(self.course_id),
            "resume_data": self.resume_data,
            "is_completed": self.is_completed,
            "is_first_start": self.is_first_start,
        }

    @classmethod
    def from_model(cls, progress_model):
        """Convert từ UserBlockProgress Model -> Domain"""
        # Giả định quan hệ: block -> lesson -> module -> course
        block = progress_model.block
        lesson = block.lesson
        module = lesson.module
        
        return cls(
            block_id=block.id,
            lesson_id=lesson.id,
            module_id=module.id,
            course_id=module.course_id,

            resume_data=progress_model.resume_data,
            is_completed=progress_model.is_completed,
            is_first_start=False,

            user_id=progress_model.user_id,
            last_accessed=progress_model.last_accessed
        )

    @classmethod
    def from_first_block(cls, block_model, user_id):
        """Convert từ ContentBlock Model (trường hợp học viên mới) -> Domain"""
        lesson = block_model.lesson
        module = lesson.module

        return cls(
            block_id=block_model.id,
            lesson_id=lesson.id,
            module_id=module.id,
            course_id=module.course_id,

            resume_data={},     # Mới tinh, chưa có data
            is_completed=False,
            is_first_start=True,

            user_id=user_id,
            last_accessed=None
        )