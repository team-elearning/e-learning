from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from progress.domains.resume_point_domain import ResumePointDomain



@dataclass
class CourseCardDomain:
    """
    Thẻ khóa học trên Dashboard học viên (My Learning).
    """
    course_id: str
    title: str
    thumbnail: Optional[str]
    owner_name: str
    
    # Tiến độ
    percent_completed: float
    is_completed: bool
    last_accessed_at: datetime
    
    # Trạng thái hiển thị (Moodle Style)
    # 'not_started' (0%), 'in_progress', 'completed'
    display_status: str 
    
    # Điểm quay lại học (Resume Button)
    resume_point: Optional[ResumePointDomain]