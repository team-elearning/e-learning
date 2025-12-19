from dataclasses import dataclass
from typing import Optional



@dataclass
class VideoEngagementDomain:
    """
    Kết quả phân tích hành vi xem Video cụ thể.
    """
    user_id: str
    content_block_id: str
    video_title: str
    video_duration: int
    
    # Metrics định lượng
    total_time_spent: int    # Tổng thời gian thực tế user ở lại trang xem video (giây)
    actual_watch_time: int   # Tổng thời gian video chạy (không tính lúc pause)
    max_timestamp_reached: int # User xem đến giây thứ bao nhiêu (để tính % thực)
    
    # Metrics hành vi
    play_count: int          # Số lần bấm play (Resume nhiều lần?)
    pause_count: int         # Số lần pause (Ghi chép?)
    seek_forward_count: int  # Tua đi (Lướt)
    seek_backward_count: int # Tua lại (Học kỹ/Không hiểu)
    
    # Kết luận AI (Behavior Classification)
    learning_style: str      # 'deep_learner', 'skimmer', 'passive', 'dropout'
    engagement_quality: float # 0.0 -> 10.0 (Chất lượng buổi học)
    insight_text: str        # "Học viên tua lại nhiều ở phút 05:30"