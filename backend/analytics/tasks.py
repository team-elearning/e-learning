import traceback
from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from typing import Dict, Any, Optional

from custom_account.models import UserModel
from analytics.services.course_analyze_service import analyze_course_health_bulk
from analytics.models import UserActivityLog, CourseAnalyticsLog
from gamification.models import UserGamification



@shared_task
def async_log_activity(user_id: int, data: Dict[str, Any]):
    """
    Celery Task: Chạy ở background worker.
    1. Ghi log vào DB (UserActivityLog).
    2. Cập nhật Streak (UserGamification).
    """
    try:
        from analytics.services.log_service import _save_to_db

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


@shared_task
def async_log_batch(user_id: int, data_list: list):
    """
    Worker xử lý Bulk Insert.
    data_list: List các dict đã được clean và serialize.
    """
    if not data_list:
        return

    try:
        user = UserModel.objects.get(id=user_id)
        log_instances = []
        
        # 1. Convert Dict -> Model Instances
        for data in data_list:
            # Lưu ý: data ở đây là dict thuần (JSON), cần convert lại nếu có field đặc biệt
            # Ở đây giả sử _validate_and_normalize đã trả về dict khớp với Model fields
            log_instances.append(UserActivityLog(
                user=user,
                action=data.get('action'),
                entity_type=data.get('entity_type'),
                entity_id=data.get('entity_id'),
                payload=data.get('payload', {}),
                session_id=data.get('session_id'),
                # timestamp sẽ tự động lấy now() nhờ auto_now_add trong Model
                # Trừ khi bạn muốn ghi đè timestamp từ client gửi lên (cần parse datetime string)
            ))
            
        # 2. Bulk Create (1 Query duy nhất cho N dòng)
        if log_instances:
            UserActivityLog.objects.bulk_create(log_instances, batch_size=500)
            
            # 3. [OPTIMIZATION] Update Streak
            # Thay vì update N lần cho N log, ta chỉ update 1 lần duy nhất cho cả Batch
            # Vì dù user có xem 10 segment video trong 1 phút thì cũng chỉ tính là 1 lần học hôm nay.
            update_streak_on_activity_logic(user)
            
            print(f"✅ Bulk logged {len(log_instances)} activities for User {user_id}")
            
    except UserModel.DoesNotExist:
        pass
    except Exception as e:
        print(f"❌ Error in async_log_batch: {e}")


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


@shared_task
def async_analyze_course(course_id: str):
    """
    Task chạy ngầm phân tích sức khỏe lớp học.
    """
    try:
        result = analyze_course_health_bulk(course_id)
        
        # A. LƯU LOG THÀNH CÔNG
        CourseAnalyticsLog.objects.create(
            course_id=course_id,
            total_students=result.total_students,
            processed_count=result.processed_count,
            status='success',
            execution_time_seconds=result.execution_time
        )

        # [OPTIONAL] Gửi Notification cho giáo viên qua WebSocket/Email
        # send_notification(owner_id, "Phân tích lớp học đã hoàn tất!")
        
        # B. GỬI THÔNG BÁO (Ví dụ)
        # NotificationService.send(
        #    user_id=owner_id, 
        #    title="Phân tích hoàn tất",
        #    body=f"Đã phân tích xong {result.processed_count} học viên."
        # )
        
        print(f"✅ Job Success: Course {course_id}")

    except Exception as e:
        # C. LƯU LOG THẤT BẠI (Quan trọng để debug)
        error_msg = str(e) + "\n" + traceback.format_exc()
        
        CourseAnalyticsLog.objects.create(
            course_id=course_id,
            status='failed',
            error_message=error_msg[:5000] # Cắt bớt nếu quá dài
        )
        print(f"❌ Job Failed: {e}")