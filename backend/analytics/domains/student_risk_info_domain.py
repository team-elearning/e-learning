import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime



logger = logging.getLogger(__name__)

@dataclass
class StudentRiskInfoDomain:
    """
    Domain thống nhất: Chứa toàn bộ thông tin về sức khỏe học tập của 1 user.
    Dùng cho cả lúc Phân tích (Ghi) và Hiển thị (Đọc).
    """
    # Định danh
    user_id: str
    course_id: str
    full_name: str
    email: str
    avatar_url: Optional[str]
    
    # Chỉ số (Metrics)
    engagement_score: float
    performance_score: float
    days_inactive: int
    last_access_days: int 
    
    # Kết luận AI
    risk_level: str          # 'low', 'medium', 'high', 'critical'
    ai_insight: str              # Message/Lý do
    suggested_action: str

    # Số liệu thực tế bổ sung (Realtime join)
    real_percent_completed: float
    last_login_at: Optional[datetime]

    @classmethod
    def from_snapshot_model(cls, snapshot_model: Any, course_id: str) -> Optional['StudentRiskInfoDomain']:
        """
        Factory Method: Tạo Domain từ Django Model Instance (đã được annotate).
        Trả về None nếu dữ liệu nguồn bị lỗi.
        """
        try:
            # 1. Lấy User an toàn
            user_obj = getattr(snapshot_model, 'user', None)
            if not user_obj:
                logger.warning(f"Snapshot {snapshot_model.id} missing user relationship.")
                return None

            # 2. Lấy dữ liệu Annotated (từ Subquery)
            # Nếu không có (do quên annotate ở service), mặc định là 0.0
            percent = getattr(snapshot_model, 'real_percent_completed', 0.0) or 0.0

            # 3. Construct Object
            return cls(
                user_id=str(user_obj.id),
                course_id=str(course_id),
                full_name=getattr(user_obj, 'username', 'Unknown'),
                email=getattr(user_obj, 'email', ''),
                avatar_url=None, # Todo: Logic lấy avatar
                
                engagement_score=snapshot_model.engagement_score,
                performance_score=snapshot_model.performance_score,
                days_inactive=snapshot_model.days_inactive,
                last_access_days=snapshot_model.days_inactive,
                
                risk_level=snapshot_model.risk_level,
                ai_insight=snapshot_model.ai_message,
                suggested_action=snapshot_model.suggested_action,
                
                real_percent_completed=percent,
                last_login_at=None # Todo: Lấy từ user_obj.last_login
            )
            
        except Exception as e:
            # Log lỗi nhưng không crash app, trả về None để skip dòng này
            logger.error(f"Error mapping Snapshot {getattr(snapshot_model, 'id', 'unknown')} to Domain: {e}", exc_info=True)
            return None