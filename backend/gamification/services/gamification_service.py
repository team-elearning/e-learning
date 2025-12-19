from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from typing import List

from analytics.models import UserActivityLog
from gamification.domains.streak_domain import StreakDomain
from gamification.models import UserGamification



# ==========================================
# PUBLIC INTERFACE (HELPER)
# ==========================================

def _get_motivational_message(self, streak, is_active_today):
    if streak == 0:
        return "Hãy bắt đầu chuỗi ngày học tập ngay hôm nay!"
    
    if is_active_today:
        return f"Tuyệt vời! Bạn đã duy trì chuỗi {streak} ngày! 🔥"
        
    # Nếu chưa học hôm nay
    return f"Bạn đang có chuỗi {streak} ngày. Đừng để đứt chuỗi nhé! ⚠️"


# ==========================================
# PUBLIC INTERFACE (GET STREAK)
# ==========================================

def get_user_streak(user_id: str) -> StreakDomain:
    """
    Tính Streak.
    """
    # 1. Lấy trạng thái đã lưu
    # Dùng get_or_create để handle trường hợp user mới tinh chưa có record
    gamification, created = UserGamification.objects.get_or_create(
        user_id=user_id,
        defaults={'current_streak': 0, 'longest_streak': 0}
    )

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    last_date = gamification.last_activity_date
    current_streak = gamification.current_streak
    is_active_today = (last_date == today)

    if not last_date:
        # User mới chưa học gì
        current_streak = 0

    elif last_date < yesterday:
        # Đã quá hạn (lần cuối học cách đây 2 ngày trở lên)
        # -> Streak thực tế đã về 0, dù DB vẫn lưu số cũ (do user chưa login lại để trigger update)
        # Ta hiển thị 0 cho user thấy
        current_streak = 0
        
        # [Optional] Có thể update ngầm lại DB về 0 ở đây nếu muốn clean data, 
        # nhưng thường thì để hàm update_streak_on_activity xử lý khi user học lại sẽ tốt hơn (Lazy Write).

    msg = _get_motivational_message(current_streak, is_active_today)

    return StreakDomain(
        current_streak=current_streak,
        longest_streak=gamification.longest_streak,
        last_activity_date=last_date,
        is_active_today=is_active_today,
        message=msg
    )

