import logging
from celery import shared_task
from django.utils import timezone

from custom_account.models import UserModel
from content.models import ContentBlock, Enrollment, Lesson
from progress.models import QuizAttempt, UserBlockProgress, LessonCompletion
from analytics.services.log_service import record_activity



logger = logging.getLogger(__name__)

@shared_task
def calculate_aggregation(enrollment_id: str, lesson_id: str):
    """
    Hàm này chạy NẶNG, chuyên để tính toán Domino:
    Block Done -> Check Lesson -> Check Module -> Check Course
    """
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id)
        lesson = Lesson.objects.get(id=lesson_id)
    except (Enrollment.DoesNotExist, Lesson.DoesNotExist):
        return

    # --- 1. DOMINO CẤP LESSON ---
    # Đếm số block đã xong trong lesson này
    total_blocks = ContentBlock.objects.filter(lesson=lesson).count()
    completed_blocks = UserBlockProgress.objects.filter(
        enrollment=enrollment, 
        block__lesson=lesson, 
        is_completed=True
    ).count()

    is_lesson_completed = False
    
    if total_blocks > 0 and completed_blocks >= total_blocks:
        # Upsert LessonCompletion
        obj, created = LessonCompletion.objects.update_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={'is_completed': True, 'completed_at': timezone.now()}
        )
        if created or not obj.is_completed:
            is_lesson_completed = True

    # --- 2. DOMINO CẤP COURSE (Chỉ chạy nếu lesson vừa xong hoặc định kỳ) ---
    # Để tối ưu, chỉ tính lại % course nếu lesson có sự thay đổi, 
    # hoặc bạn có thể chọn luôn tính lại để đảm bảo chính xác.
    
    # Query tổng lesson
    total_lessons = Lesson.objects.filter(module__course=enrollment.course).count()
    
    # Query lesson đã xong
    completed_lessons_count = LessonCompletion.objects.filter(
        enrollment=enrollment, is_completed=True
    ).count()

    if total_lessons > 0:
        new_percent = round((completed_lessons_count / total_lessons) * 100, 2)
        new_percent = min(100.0, new_percent)

        # Update Enrollment (Dùng update_fields cho nhẹ)
        if enrollment.percent_completed != new_percent:
            enrollment.percent_completed = new_percent
            if new_percent == 100:
                enrollment.is_completed = True
                enrollment.completed_at = timezone.now()
            
            enrollment.save(update_fields=['percent_completed', 'is_completed', 'completed_at'])


def _safe_trigger_async_task(attempt_id, user_id, course_id):
    """Helper function để gửi task an toàn, không làm sập app nếu Broker chết."""
    try:
        async_update_course_progress_and_analytics.delay(
            attempt_id=attempt_id,
            user_id=user_id,
            course_id=course_id
        )
    except Exception as e:
        # Log lỗi nhưng KHÔNG raise exception
        # Có thể lưu vào bảng FailedTask để retry sau (nếu cần thiết)
        logger.error(f"⚠️ Failed to trigger async task (Broker down?): {e}")


@shared_task
def async_update_course_progress_and_analytics(attempt_id, user_id, course_id):
    """
    Task chạy ngầm sau khi nộp bài.
    Nhiệm vụ:
    1. Đánh dấu Block Quiz là 'Completed' trong bảng UserBlockProgress.
    2. Tính lại % khóa học.
    3. Ghi log tracking.
    """
    from progress.services.course_tracking_service import mark_quiz_as_completed
    
    try:
        # Fetch attempt tối ưu (chỉ lấy field cần thiết)
        attempt = QuizAttempt.objects.filter(id=attempt_id).only(
            'id', 'quiz_id', 'enrollment_id', 'score', 'is_passed'
        ).first()
        
        if not attempt: 
            return

        # 1. Update Block Progress (Chỉ nếu PASS)
        completed_lesson_id = None
        if attempt.is_passed:
            completed_lesson_id = mark_quiz_as_completed(
                user_id=user_id,
                quiz_id=attempt.quiz_id,
                enrollment_id=attempt.enrollment_id,
                score=attempt.score
            )

        # 2. Aggregation (Chỉ tính lại % nếu có tiến độ mới)
        # Điều này giúp giảm tải DB cực lớn, không tính lại nếu user làm lại bài thi cũ
        if completed_lesson_id:
            # Logic tìm lesson_id có thể lấy từ BlockCompletionService hoặc query nhẹ
            # Giả sử ta biết lesson_id từ block (trong thực tế nên return từ mark_quiz_as_completed)
            # Ở đây gọi hàm aggregation của bạn
            calculate_aggregation(
                enrollment_id=str(attempt.enrollment_id), 
                lesson_id=completed_lesson_id
            )
       
        # # 3. Notification (Optional)
        # # Nếu pass -> Gửi mail chúc mừng / Cấp chứng chỉ
        # attempt = QuizAttempt.objects.get(id=attempt_id)
        # if attempt.is_passed:
        #     notification_service.notify_quiz_passed(user_id, attempt.quiz.title)

    except Exception as e:
        logger.error(f"Error async update quiz progress: {e}")