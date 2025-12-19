from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, date



@dataclass
class DailyMetricDomain:
    """
    Dữ liệu của 1 ngày cụ thể. Dùng để vẽ 1 điểm trên biểu đồ Line Chart.
    """
    date: str               # YYYY-MM-DD
    avg_engagement: float   # Điểm chuyên cần trung bình ngày đó
    avg_performance: float  # Điểm thành tích trung bình ngày đó