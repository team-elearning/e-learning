# services/aggregation_service.py
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from content.models import Lesson, Enrollment, ContentBlock
from progress.models import UserBlockProgress, LessonCompletion



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