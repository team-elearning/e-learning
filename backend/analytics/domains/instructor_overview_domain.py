from typing import List, Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

from analytics.domains.daily_metric_domain import DailyMetricDomain
from analytics.domains.course_health_overview_domain import CourseHealthOverviewDomain



class InstructorOverviewDomain(BaseModel):
    """
    Domain object tổng hợp Dashboard cho Instructor.
    """
    instructor_id: str

    # --- Headline Stats (Thống kê tổng quan) ---
    total_revenue: Decimal = Field(..., description="Tổng doanh thu toàn thời gian")
    total_students: int = Field(..., description="Tổng số học viên (unique)")
    total_enrollments: int = Field(..., description="Tổng lượt ghi danh")
    active_courses_count: int = Field(..., description="Số khóa học đang public")

    # --- Global Health (Sức khỏe chung) ---
    global_engagement: float = Field(..., description="Điểm tương tác trung bình (0-100)")
    global_performance: float = Field(..., description="Điểm học lực trung bình (0-100)")
    critical_students_total: int = Field(..., description="Tổng số snapshot có rủi ro cao/nghiêm trọng")

    # --- Charts & Lists ---
    chart_data: List[DailyMetricDomain] = Field(default_factory=list, description="Dữ liệu biểu đồ 7 ngày qua")
    
    top_performing_courses: List[CourseHealthOverviewDomain] = Field(
        default_factory=list, 
        description="Top khóa học tốt nhất (theo doanh thu hoặc rating)"
    )
    
    courses_needing_attention: List[CourseHealthOverviewDomain] = Field(
        default_factory=list, 
        description="Các khóa học cần lưu ý (có nhiều học viên rủi ro)"
    )

    class Config:
        from_attributes = True # Cho phép map từ ORM nếu cần sau này