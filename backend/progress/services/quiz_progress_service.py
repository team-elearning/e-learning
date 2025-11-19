# tracking/services/tracking_service.py

from django.db import transaction
from django.db.models import Count, Q
from core.exceptions import DomainError
from content.models import ContentBlock, Lesson, Course # Import model content
from progress.models import BlockCompletion, LessonCompletion, CourseProgress
from progress.domains import LessonTrackingDomain, BlockCompletionDomain, CourseProgressDomain
import uuid

def get_course_progress_summary(self, user, course_id: uuid.UUID) -> CourseProgressDomain:
        """Lấy tổng quan tiến độ khóa học cho Dashboard."""
        progress, _ = CourseProgress.objects.get_or_create(
            user=user, course_id=course_id
        )
        return CourseProgressDomain.from_model(progress)

    def get_lesson_tracking_status(self, user, lesson_id: uuid.UUID) -> LessonTrackingDomain:
        """
        Lấy trạng thái chi tiết của 1 Lesson (để merge vào Content khi hiển thị).
        """
        # 1. Lấy tất cả Block ID trong lesson này (từ Content App)
        # Lưu ý: Chỉ lấy ID để tối ưu query
        block_ids = ContentBlock.objects.filter(lesson_id=lesson_id).values_list('id', flat=True)
        
        # 2. Lấy các record completion đã có của user
        completions = BlockCompletion.objects.filter(
            user=user, block_id__in=block_ids
        )
        completion_map = {c.block_id: c for c in completions}
        
        # 3. Build Domain List
        block_domains = []
        completed_count = 0
        
        for b_id in block_ids:
            comp = completion_map.get(b_id)
            is_done = comp.is_completed if comp else False
            data = comp.interaction_data if comp else {}
            
            if is_done:
                completed_count += 1
                
            block_domains.append(BlockCompletionDomain(
                block_id=b_id,
                is_completed=is_done,
                interaction_data=data
            ))

        # 4. Tính toán % lesson
        total_blocks = len(block_ids)
        percent = (completed_count / total_blocks * 100) if total_blocks > 0 else 0.0
        
        # Lấy trạng thái lesson tổng
        lesson_comp, _ = LessonCompletion.objects.get_or_create(
            user=user, lesson_id=lesson_id,
            defaults={'course_id': uuid.uuid4(), 'module_id': uuid.uuid4()} # Placeholder, logic update sau
        )

        return LessonTrackingDomain(
            lesson_id=lesson_id,
            is_completed=lesson_comp.is_completed,
            percent_completed=round(percent, 2),
            blocks=block_domains
        )

    @transaction.atomic
    def sync_block_progress(
        self, user, lesson_id: uuid.UUID, block_id: uuid.UUID, 
        is_completed: bool, interaction_data: dict
    ) -> BlockCompletionDomain:
        """
        [HEARTBEAT] Hàm quan trọng nhất. Update tiến độ block và tính toán lan truyền (Cascade).
        """
        # 1. Update BlockCompletion
        block_comp, created = BlockCompletion.objects.update_or_create(
            user=user, block_id=block_id,
            defaults={
                'lesson_id': lesson_id,
                'interaction_data': interaction_data,
                'is_completed': is_completed
            }
        )
        
        # Nếu hoàn thành là True, ghi nhận thời gian
        if is_completed and not block_comp.completed_at:
            from django.utils import timezone
            block_comp.completed_at = timezone.now()
            block_comp.save()

        # 2. [CASCADE CHECK] Kiểm tra xem Lesson đã hoàn thành chưa?
        # Logic Moodle: Lesson hoàn thành khi TẤT CẢ blocks hoàn thành.
        self._check_and_update_lesson_completion(user, lesson_id)

        return BlockCompletionDomain.from_model(block_comp)

    def _check_and_update_lesson_completion(self, user, lesson_id):
        """Logic kiểm tra hoàn thành bài học."""
        # Lấy tổng số block
        total_blocks = ContentBlock.objects.filter(lesson_id=lesson_id).count()
        
        # Lấy số block đã hoàn thành
        completed_blocks = BlockCompletion.objects.filter(
            user=user, lesson_id=lesson_id, is_completed=True
        ).count()

        is_lesson_done = (completed_blocks >= total_blocks) and (total_blocks > 0)
        
        if is_lesson_done:
            # Lấy info để update (cần course_id từ lesson)
            lesson = Lesson.objects.select_related('module__course').get(id=lesson_id)
            course_id = lesson.module.course.id
            module_id = lesson.module.id

            lesson_comp, created = LessonCompletion.objects.update_or_create(
                user=user, lesson_id=lesson_id,
                defaults={
                    'is_completed': True,
                    'course_id': course_id,
                    'module_id': module_id
                }
            )
            # 3. [CASCADE CHECK] Kiểm tra xem Course đã hoàn thành chưa?
            self._check_and_update_course_progress(user, course_id)

    def _check_and_update_course_progress(self, user, course_id):
        """Logic tính % hoàn thành khóa học."""
        # Tổng số lessons trong khóa học
        total_lessons = Lesson.objects.filter(module__course_id=course_id).count()
        
        # Tổng số lessons user đã hoàn thành
        completed_lessons = LessonCompletion.objects.filter(
            user=user, course_id=course_id, is_completed=True
        ).count()
        
        percent = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0.0
        is_course_done = (percent >= 100.0)

        CourseProgress.objects.update_or_create(
            user=user, course_id=course_id,
            defaults={
                'percent_completed': round(percent, 2),
                'is_completed': is_course_done
            }
        )