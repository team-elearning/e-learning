from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from typing import Dict, Any, Optional

from custom_account.models import UserModel
from analytics.services.log_service import _save_to_db
from gamification.models import UserGamification



@shared_task
def async_log_activity(user_id: int, data: Dict[str, Any]):
    """
    Celery Task: Chạy ở background worker.
    1. Ghi log vào DB (UserActivityLog).
    2. Cập nhật Streak (UserGamification).
    """
    try:
        # 1. Re-hydrate User: Lấy lại object User từ ID
        user = UserModel.objects.get(pk=user_id)
        
        # 2. Gắn lại user vào data để hàm _save_to_db dùng được
        data['user'] = user
        
        # 3. Gọi hàm lưu DB (Tái sử dụng logic cũ)
        _save_to_db(data)

        # 2. [NEW] Cập nhật Streak ngay sau khi ghi log
        # Chỉ update nếu hành động mang tính chất "Học tập" (tránh việc login vào chơi cũng tính streak)
        # Moodle/Duolingo thường chỉ tính khi hoàn thành bài học hoặc xem video > 1 phút.
        # Ở đây tạm thời ta tính cho mọi activity, hoặc bạn có thể filter action.
        
        IGNORE_ACTIONS = ['SEARCH', 'LOGOUT'] # Ví dụ các hành động không tính streak
        
        if data.get('action') not in IGNORE_ACTIONS:
            update_streak_on_activity_logic(user)
        
    except UserModel.DoesNotExist:
        print(f"⚠️ Async Log Error: User ID {user_id} not found.")
    except Exception as e:
        print(f"⚠️ Async Log Task Error: {e}")


def update_streak_on_activity_logic(user):
    gamification, _ = UserGamification.objects.get_or_create(user=user)
    today = timezone.now().date()
    
    # 1. Nếu hôm nay đã tính rồi -> Bỏ qua ngay (Debounce)
    if gamification.last_activity_date == today:
        return 
        
    yesterday = today - timedelta(days=1)
    
    # 2. Logic cập nhật
    if gamification.last_activity_date == yesterday:
        # Nối dài chuỗi
        gamification.current_streak += 1
    elif gamification.last_activity_date and gamification.last_activity_date < yesterday:
        # Đứt chuỗi
        if gamification.freeze_equipped:
            # Dùng bảo băng
            gamification.freeze_equipped = False
            # Streak giữ nguyên, chỉ update ngày
        else:
            # Reset
            gamification.current_streak = 1
    else:
        # Lần đầu tiên (hoặc user mới)
        gamification.current_streak = 1
        
    # Update Max & Save
    if gamification.current_streak > gamification.longest_streak:
        gamification.longest_streak = gamification.current_streak
        
    gamification.last_activity_date = today
    gamification.save()