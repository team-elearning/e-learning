import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# Create your models here.
class Progress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='progresses')
    lesson = models.ForeignKey('content.Lesson', on_delete=models.CASCADE, related_name='progresses')
    lesson_version = models.ForeignKey('content.LessonVersion', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=32,
        default='not_started',
        choices=[('not_started', ('Not Started')), ('in_progress', ('In Progress')), ('completed', ('Completed'))]
    )
    percent = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    last_interaction = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'lesson')
        verbose_name = ('Progress')
        verbose_name_plural = ('Progresses')

    def __str__(self):
        return f"Progress for {self.lesson} by {self.student}"

class Event(models.Model):
    # Analytics events (Oppia-style logging).
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    event_type = models.CharField(max_length=128)  # e.g., 'lesson_view', 'exercise_complete'
    object_type = models.CharField(max_length=64)  # e.g., 'lesson', 'exploration'
    object_id = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['event_type', 'created_at'])]
        verbose_name = ('Event')
        verbose_name_plural = ('Events')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} by {self.user}"