from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional



@dataclass
class StudentRiskProfile:
    """
    Kết quả khám bệnh cho học viên.
    """
    user_id: str
    course_id: str
    
    # Các chỉ số (Metrics)
    engagement_score: float   # 0.0 -> 10.0 (Độ nhiệt tình)
    performance_score: float  # 0.0 -> 10.0 (Điểm số/Kết quả)
    last_access_days: int     # Số ngày chưa quay lại học
    
    # Kết luận của AI
    risk_level: str           # 'low', 'medium', 'high', 'critical'
    status_label: str         # 'Học viên gương mẫu', 'Cần nhắc nhở', 'Nguy cơ bỏ học'
    
    # Hành động gợi ý (Prescription)
    suggested_action: str     # 'send_email', 'recommend_easier_content', 'none'
    message: str              # Nội dung gợi ý chi tiết