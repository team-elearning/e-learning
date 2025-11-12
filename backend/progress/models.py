import uuid
from django.db import models
from django.conf import settings
from content.models import Course, Lesson

# class Enrollment(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
#     course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
#     enrolled_at = models.DateTimeField(auto_now_add=True)
#     completed_at = models.DateTimeField(null=True, blank=True)

#     class Meta:
#         unique_together = ('user', 'course')
#         ordering = ['-enrolled_at']
#         verbose_name = 'Enrollment'
#         verbose_name_plural = 'Enrollments'

#     def __str__(self):
#         return f"{self.user} enrolled in {self.course}"

# class LessonProgress(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress')
#     lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
#     completed_at = models.DateTimeField(null=True, blank=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         unique_together = ('enrollment', 'lesson')
#         verbose_name = 'Lesson Progress'
#         verbose_name_plural = 'Lesson Progress'

#     def __str__(self):
#         status = "Completed" if self.completed_at else "In Progress"
#         return f"Progress for {self.enrollment.user} in {self.lesson.title}: {status}"