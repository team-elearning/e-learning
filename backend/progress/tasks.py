import logging
from celery import shared_task
from django.db.models import F
from django.db.models.functions import Round 
from django.utils import timezone

from custom_account.models import UserModel
from content.models import ContentBlock, Enrollment, Lesson
from progress.models import QuizAttempt, UserBlockProgress, LessonCompletion, ModuleCompletion
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
        module = lesson.module
        course = module.course
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

    is_lesson_just_finished = False
    
    if total_blocks > 0 and completed_blocks >= total_blocks:
        # Upsert LessonCompletion
        obj, created = LessonCompletion.objects.update_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={'is_completed': True, 'completed_at': timezone.now()}
        )
        if created or not obj.is_completed:
            is_lesson_just_finished = True

    if not is_lesson_just_finished:
        return

    # --- 2. DOMINO CẤP COURSE (Chỉ chạy nếu lesson vừa xong hoặc định kỳ) ---
    # Để tối ưu, chỉ tính lại % course nếu lesson có sự thay đổi, 
    # hoặc bạn có thể chọn luôn tính lại để đảm bảo chính xác.
    total_lessons_in_module = Lesson.objects.filter(module=module).count()

    completed_lessons_in_module = LessonCompletion.objects.filter(
        enrollment=enrollment,
        lesson__module=module,
        is_completed=True
    ).count()

    if total_lessons_in_module > 0 and completed_lessons_in_module == total_lessons_in_module:
        # Đánh dấu Module đã xong
        ModuleCompletion.objects.get_or_create(
            enrollment=enrollment,
            module=module,
            defaults={'is_completed': True, 'completed_at': timezone.now()}
        )
        # TODO: Tại đây có thể trigger sự kiện "Unlock Module Tiếp Theo" nếu có logic đó.
    
    # Query tổng lesson
    total_lessons_course = Lesson.objects.filter(module__course=course).count()
    
    # Query lesson đã xong
    completed_lessons_course = LessonCompletion.objects.filter(
        enrollment=enrollment, is_completed=True
    ).count()

    enrollment.cached_total_lessons = total_lessons_course
    enrollment.cached_completed_lessons = completed_lessons_course

    if total_lessons_course > 0:
        new_percent = round((completed_lessons_course / total_lessons_course) * 100, 2)
        new_percent = min(100.0, new_percent)

        # Update Enrollment (Dùng update_fields cho nhẹ)
        if enrollment.percent_completed != new_percent:
            enrollment.percent_completed = new_percent
            if new_percent == 100:
                enrollment.is_completed = True
                enrollment.completed_at = timezone.now()
            
            enrollment.save(update_fields=[
                'percent_completed', 
                'cached_total_lessons', 
                'cached_completed_lessons',
                'is_completed', 
                'completed_at'
            ])


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


@shared_task
def process_content_addition_impact(lesson_id):
    """
    Hàm xử lý hậu quả khi thêm ContentBlock vào một Lesson.
    Logic: 
    1. Lesson đang 'Completed' -> Phải chuyển thành 'Incomplete'.
    2. Enrollment đang '100%' -> Phải tụt % và mất trạng thái 'Completed'.
    """
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        course = lesson.module.course
    except Lesson.DoesNotExist:
        return

    # -------------------------------------------------------
    # 1. TÌM CÁC HỌC VIÊN ĐÃ HỌC XONG LESSON NÀY
    # -------------------------------------------------------
    # Những người này trước đây completed_blocks == total_blocks (cũ).
    # Giờ total_blocks (mới) tăng lên, nên họ trở thành chưa xong.
    affected_lesson_completions = LessonCompletion.objects.filter(
        lesson=lesson,
        is_completed=True
    )
    
    affected_enrollment_ids = list(affected_lesson_completions.values_list('enrollment_id', flat=True))
    logger.info(f"helooooooooooooooooooooooooooo {len(affected_enrollment_ids)}")

    if not affected_enrollment_ids:
        return # Không có ai bị ảnh hưởng

    # -------------------------------------------------------
    # 2. RESET TRẠNG THÁI LESSON (Bulk Update)
    # -------------------------------------------------------
    # Chuyển lesson về chưa hoàn thành
    affected_lesson_completions.update(is_completed=False, completed_at=None)

    # -------------------------------------------------------
    # 3. CẬP NHẬT ENROLLMENT (Bulk Update - Rất quan trọng để tối ưu)
    # -------------------------------------------------------
    # Logic:
    # - cached_completed_lessons: Giảm đi 1 (do lesson này vừa bị đánh dấu chưa xong)
    # - is_completed: Chắc chắn False (vì ít nhất 1 lesson chưa xong)
    # - percent_completed: Tính lại.
    
    # Lưu ý: Việc tính lại chính xác % cho hàng nghìn user bằng 1 câu lệnh SQL
    # hơi phức tạp nếu số lesson khác nhau (dynamic). 
    # Cách an toàn và nhanh nhất ở đây là dùng F expression để giảm count,
    # sau đó tính tương đối hoặc trigger tính lại.
    
    # Ở đây tôi chọn cách update count và reset flag trước (nhanh nhất).
    # Việc tính lại % chính xác tuyệt đối có thể để User tự trigger khi họ vào học tiếp,
    # HOẶC tính toán ngay tại đây nếu cần hiển thị đúng ngay lập tức.
    
    # Lấy tổng số lesson hiện tại của Course
    total_lessons = Lesson.objects.filter(module__course=course).count()
    logger.info(f"tổng số lesson hiện tại của Course {total_lessons}")
    
    if total_lessons > 0:
        # Giảm số lesson đã hoàn thành đi 1 cho tất cả user bị ảnh hưởng
        Enrollment.objects.filter(id__in=affected_enrollment_ids).update(
            cached_completed_lessons=F('cached_completed_lessons') - 1,
            is_completed=False,
            completed_at=None
            # percent_completed: Tạm thời chưa update ngay để tránh lock bảng quá lâu
            # hoặc update bằng công thức SQL bên dưới
        )

        # (Optional) Update Percent ngay lập tức bằng SQL Expression
        # percent = (cached_completed_lessons / total_lessons) * 100
        Enrollment.objects.filter(id__in=affected_enrollment_ids).update(
            percent_completed=Round(
                (F('cached_completed_lessons') * 100.0) / total_lessons, 
                2
            )
        )


@shared_task
def process_lesson_addition_impact(course_id):
    """
    Chạy ngầm khi giáo viên tạo Lesson mới.
    Logic:
    1. Update lại cached_total_lessons cho toàn bộ Enrollment.
    2. Reset trạng thái is_completed = False (vì vừa mọc ra bài mới chưa học).
    3. Tính lại % hoàn thành dựa trên mẫu số mới.
    """
    # Lấy chính xác tổng số lesson hiện tại trong DB
    # Lưu ý: Lúc này transaction bên ngoài đã commit, nên count sẽ bao gồm bài vừa tạo.
    new_total_lessons = Lesson.objects.filter(module__course_id=course_id).count()

    if new_total_lessons == 0:
        return

    # BULK UPDATE: Cực nhanh, xử lý hàng nghìn user trong tích tắc
    # Công thức: percent = (đã_học / tổng_mới) * 100
    Enrollment.objects.filter(course_id=course_id).update(
        cached_total_lessons=new_total_lessons,
        is_completed=False,  # Chắc chắn chưa xong vì có bài mới
        completed_at=None,   # Reset ngày hoàn thành
        percent_completed=Round(
            (F('cached_completed_lessons') * 100.0) / new_total_lessons, 
            2
        )
    )