from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any



@dataclass
class AnalyticsLogDomain:
    """Lịch sử chạy Job"""
    job_id: int
    status: str
    processed_students: int
    execution_time: float
    run_at: datetime
    error_detail: Optional[str] = None