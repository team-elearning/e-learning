from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime



@dataclass
class StudentRiskInfoDomain:
    """
    Domain thống nhất: Chứa toàn bộ thông tin về sức khỏe học tập của 1 user.
    Dùng cho cả lúc Phân tích (Ghi) và Hiển thị (Đọc).
    """
    # Định danh
    user_id: str
    course_id: str
    
    # Chỉ số (Metrics)
    engagement_score: float
    performance_score: float
    days_inactive: int
    
    # Kết luận AI
    risk_level: str          # 'low', 'medium', 'high', 'critical'
    reason: str              # Message/Lý do
    suggested_action: str
    
    # Thông tin UI (Optional - chỉ cần khi hiển thị Dashboard)
    student_name: Optional[str] = None
    student_avatar: Optional[str] = None
    last_updated: Optional[datetime] = None