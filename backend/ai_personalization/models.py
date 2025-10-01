import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator



# Create your models here.
class LearningPath(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learning_paths')
    course = models.ForeignKey('content.Course', on_delete=models.CASCADE, related_name='learning_paths')
    path = models.JSONField(default=list)  # e.g., [{'lesson_id': 'uuid', 'order': 1}, ...]
    generated_at = models.DateTimeField(auto_now_add=True)
    ai_model = models.CharField(max_length=128, blank=True, null=True)  # e.g., 'gpt-4'
    metadata = models.JSONField(default=dict)  # e.g., {'based_on': 'weak_points'}

    class Meta:
        unique_together = ('student', 'course')
        verbose_name = ('Learning Path')
        verbose_name_plural = ('Learning Paths')

    def __str__(self):
        return f"Path for {self.course} by {self.student}"

class Recommendation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendations')
    recommended_lesson = models.ForeignKey('content.Lesson', on_delete=models.CASCADE, related_name='recommendations')
    score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    reason = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = ('Recommendation')
        verbose_name_plural = ('Recommendations')
        ordering = ['-score']

    def __str__(self):
        return f"Recommend {self.recommended_lesson} to {self.student}"