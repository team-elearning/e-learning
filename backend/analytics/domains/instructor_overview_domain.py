from dataclasses import dataclass
from typing import List, Dict, Optional

from analytics.domains.daily_metric_domain import DailyMetricDomain
from analytics.domains.course_summary_domain import CourseSummaryDomain



@dataclass
class InstructorOverviewDomain:
    """
    Toàn cảnh dashboard của giảng viên.
    """
    instructor_id: str
    
    # 1. Headline Stats (Những con số biết nói)
    total_revenue: int          # Tổng doanh thu tạm tính
    total_students: int         # Tổng số học viên (Unique)
    total_enrollments: int      # Tổng lượt ghi danh
    active_courses_count: int
    
    # 2. Global Health (Trung bình cộng tất cả khóa)
    global_engagement: float
    global_performance: float
    critical_students_total: int # Tổng số học viên báo động đỏ trên tất cả khóa
    
    # 3. Chart Data (Biểu đồ tổng hợp)
    # List các ngày, mỗi ngày chứa trung bình engagement của TOÀN BỘ khóa học
    chart_data: List[DailyMetricDomain] 
    
    # 4. Top Courses (Khóa học tiêu biểu)
    top_performing_courses: List[CourseSummaryDomain]
    courses_needing_attention: List[CourseSummaryDomain]