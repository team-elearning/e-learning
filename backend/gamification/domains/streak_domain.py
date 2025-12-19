from dataclasses import dataclass
from datetime import date
from typing import Optional



@dataclass
class StreakDomain:
    current_streak: int     # Chuỗi hiện tại
    longest_streak: int     # Chuỗi dài nhất (Kỷ lục)
    last_activity_date: Optional[date]
    is_active_today: bool   # Hôm nay đã học chưa? (Để hiện tick xanh)
    
    # Gamification message
    message: str            # "Bạn đang cháy quá! 🔥"