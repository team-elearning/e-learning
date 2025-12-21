from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any

from analytics.domains.student_risk_info_domain import StudentRiskInfoDomain



@dataclass
class PaginatedStudentListDomain:
    """Wrapper cho phân trang danh sách học sinh"""
    items: List[StudentRiskInfoDomain]
    total_count: int
    page: int
    page_size: int
    total_pages: int