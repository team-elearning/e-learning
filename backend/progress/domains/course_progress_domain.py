from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import datetime



@dataclass
class CourseProgressDomain:
    """
    Dữ liệu trả về cho API lấy tiến độ khóa học.
    Dùng cho Dashboard hoặc update UI sau khi heartbeat.
    """
    enrollment_id: UUID
    course_id: UUID
    user_id: UUID
    
    # --- Thông số tiến độ ---
    percent_completed: float
    is_completed: bool
    completed_at: Optional[datetime]
    last_accessed_at: Optional[datetime]
    enrolled_at: datetime

    completed_lessons_count: int = 0
    total_lessons_count: int = 0

    # --- Status Label (Helper cho FE) ---
    # 'not_started', 'in_progress', 'completed'
    status_label: str 

    @classmethod
    def from_model(cls, enrollment) -> 'CourseProgressDomain':
        status = 'in_progress'
        if enrollment.is_completed:
            status = 'completed'
        elif enrollment.percent_completed == 0:
            status = 'not_started'

        return cls(
            enrollment_id=enrollment.id,
            course_id=enrollment.course_id,
            user_id=enrollment.user_id,
            
            percent_completed=enrollment.percent_completed,
            is_completed=enrollment.is_completed,
            completed_at=enrollment.completed_at,
            last_accessed_at=enrollment.last_accessed_at,
            enrolled_at=enrollment.enrolled_at,

            completed_lessons_count=enrollment.cached_completed_lessons,
            total_lessons_count=enrollment.cached_total_lessons,
            
            status_label=status
        )