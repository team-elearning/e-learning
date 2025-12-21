from dataclasses import dataclass
from typing import List, Optional

from analytics.domains.daily_metric_domain import DailyMetricDomain



@dataclass
class CourseTrendDomain:
    """Domain trả về cho API /trends"""
    course_id: str
    chart_data: List[DailyMetricDomain]
    trend_engagement: str   # 'up', 'down', 'stable'
    trend_performance: str  # 'up', 'down', 'stable'
    insight_text: str