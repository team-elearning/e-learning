from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID



class CourseHealthAnalyzeInput(BaseModel):
    """
    DTO nhận options từ request body để cấu hình việc phân tích.
    """
    force_recalculate: bool = Field(default=False, description="Nếu True, bỏ qua cache và tính toán lại ngay lập tức.")
    # Có thể mở rộng thêm: date_range, specific_students...

    def to_dict(self) -> dict:
        return self.model_dump()


class AnalysisResultOutput(BaseModel):
    """
    DTO trả về kết quả tóm tắt sau khi chạy phân tích.
    """
    model_config = ConfigDict(from_attributes=True)

    course_id: str
    total_analyzed: int
    status: str
    message: str


class RiskDistributionOutput(BaseModel):
    """DTO con cho phân bố rủi ro"""
    model_config = ConfigDict(from_attributes=True)

    low: int
    medium: int
    high: int
    critical: int


class CourseHealthOverviewOutput(BaseModel):
    """
    DTO Output trả về cho Client.
    Mixin sẽ tự động map dữ liệu từ Domain sang class này.
    """
    model_config = ConfigDict(from_attributes=True)

    course_id: str
    total_students: int
    
    avg_engagement_score: float
    avg_performance_score: float
    avg_inactive_days: int
    
    risk_distribution: RiskDistributionOutput
    
    last_updated_at: Optional[datetime]
    data_status: str


class DailyMetricOutput(BaseModel):
    """DTO cho từng điểm dữ liệu trên biểu đồ"""
    model_config = ConfigDict(from_attributes=True)

    date: str
    avg_engagement: float
    avg_performance: float


class CourseTrendOutput(BaseModel):
    """
    DTO Output cho API Trends.
    Trả về dữ liệu vẽ biểu đồ và insight text.
    """
    model_config = ConfigDict(from_attributes=True)

    course_id: str
    chart_data: List[DailyMetricOutput]
    trend_engagement: str
    trend_performance: str
    insight_text: str


class StudentRiskInfoOutput(BaseModel):
    """
    DTO Output cho từng item trong danh sách học viên rủi ro.
    """
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str
    course_id: str
    full_name: str
    email: str
    avatar_url: Optional[str]
    
    engagement_score: float
    performance_score: float
    days_inactive: int
    last_access_days: int
    
    risk_level: str
    ai_insight: str
    suggested_action: str
    
    real_percent_completed: float
    last_login_at: Optional[datetime]