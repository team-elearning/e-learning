from dataclasses import dataclass
from typing import Optional

from content.domains.course_domain import CourseDomain
from progress.domains.course_progress_domain import CourseProgressDomain



@dataclass
class MyCourseDomain(CourseDomain):
    """
    Wrapper class: Mở rộng CourseDomain để chứa thêm context của User.
    """
    my_progress: Optional['CourseProgressDomain'] = None

    def __init__(self, **kwargs):
        # Lấy progress ra khỏi kwargs
        progress = kwargs.pop('my_progress', None)
        
        # Khởi tạo cha (CourseDomain) với các tham số còn lại
        super().__init__(**kwargs)
        
        # Gán context riêng
        self.my_progress = progress