from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from analytics.domains.daily_metric_domain import DailyMetricDomain
from analytics.domains.risk_distribution_domain import RiskDistributionDomain



@dataclass
class CourseHealthOverviewDomain:
    """
    Đại diện cho sức khỏe tổng quan của khóa học.
    """
    course_id: str
    status: str              # 'pending', 'ready'
    total_students: int
    
    # Các chỉ số trung bình hiện tại
    avg_engagement: float
    avg_performance: float
    avg_inactive_days: int

    # Phân phối rủi ro
    risk_distribution: RiskDistributionDomain

    # 2. Dữ liệu Time Series (7 ngày qua) - Vẽ Line Chart [NEW]
    chart_data: List[DailyMetricDomain]
    
    # [NEW] Xu hướng so với 7 ngày trước ('up', 'down', 'stable')
    trend_engagement: str    
    trend_performance: str
    
    insight_text: str

    # Metadata vận hành
    last_updated_at: Optional[datetime] = None
    data_status: str = 'up_to_date' # 'up_to_date', 'stale', 'calculating'