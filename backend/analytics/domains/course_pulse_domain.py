from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from analytics.domains.daily_metric_domain import DailyMetricDomain



@dataclass
class CoursePulseDomain:
    """
    Đại diện cho sức khỏe tổng quan của khóa học.
    """
    course_id: str
    status: str              # 'pending', 'ready'
    total_students: int
    
    # Phân phối rủi ro
    risk_distribution: Dict[str, int] # {'safe': 10, 'warning': 2, 'danger': 1}
    
    # Các chỉ số trung bình hiện tại
    avg_engagement: float
    avg_performance: float
    avg_inactive_days: int

    # 2. Dữ liệu Time Series (7 ngày qua) - Vẽ Line Chart [NEW]
    chart_data: List[DailyMetricDomain]
    
    # [NEW] Xu hướng so với 7 ngày trước ('up', 'down', 'stable')
    trend_engagement: str    
    trend_performance: str
    
    insight_text: str