from dataclasses import dataclass
from typing import List, Dict, Optional



@dataclass
class CourseSummaryDomain:
    """DTO rút gọn cho từng khóa học trong danh sách"""
    course_id: str
    title: str
    total_students: int
    avg_engagement: float
    risk_count: int
    status: str # 'active', 'draft'