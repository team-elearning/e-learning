from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count, Q
from django.utils import timezone

from progress.models import UserBlockProgress, LessonCompletion, Enrollment, Lesson



@receiver(post_save, sender=UserBlockProgress)
def on_block_completed(sender, instance, created, **kwargs):
    """
    Trigger: Khi 1 Block xong -> Check xem Lesson xong chưa?
    """
    if not instance.is_completed:
        return

    # Lấy Enrollment và Lesson hiện tại
    enrollment = instance.enrollment
    current_lesson = instance.block.lesson

    # Kiểm tra: User đã hoàn thành TẤT CẢ block trong lesson này chưa?
    # Logic: Đếm tổng block của lesson VÀ Đếm tổng block đã xong của user trong lesson đó
    
    total_blocks = current_lesson.content_blocks.count()
    completed_blocks = UserBlockProgress.objects.filter(
        enrollment=enrollment,
        block__lesson=current_lesson,
        is_completed=True
    ).count()

    if completed_blocks >= total_blocks:
        # Action: Đánh dấu Lesson xong
        LessonCompletion.objects.get_or_create(
            enrollment=enrollment,
            lesson=current_lesson,
            defaults={'is_completed': True}
        )
        # Note: Việc tạo LessonCompletion sẽ trigger tiếp signal tính % Course (Domino tiếp theo)


@receiver(post_save, sender=LessonCompletion)
def on_lesson_completed(sender, instance, created, **kwargs):
    """
    Trigger: Khi 1 Lesson xong -> Tính lại % Khóa học
    """
    if not instance.is_completed:
        return

    enrollment = instance.enrollment
    course = enrollment.course

    total_lessons = course.modules.aggregate(total=Count('lessons'))['total'] or 1
    completed_lessons = LessonCompletion.objects.filter(
        enrollment=enrollment, 
        is_completed=True
    ).count()

    percent = (completed_lessons / total_lessons) * 100
    enrollment.percent_completed = min(100.0, percent)
    
    if percent >= 100:
        enrollment.is_completed = True
        enrollment.completed_at = timezone.now()
        # Trigger cấp chứng chỉ ở đây nếu cần (Nhóm 5)
    
    enrollment.save()