import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
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
    

class LearningEvent(models.Model):
    """Event log from frontend — minimal schema to start."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learning_events')
    course = models.ForeignKey('content.Course', on_delete=models.CASCADE, null=True, blank=True)
    lesson = models.ForeignKey('content.Lesson', on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    event_type = models.CharField(max_length=64)  # e.g., 'start', 'submit', 'hint', 'skip', 'complete'
    detail = models.JSONField(default=dict)  # e.g., {'correct': True, 'attempts': 2, 'time_spent': 45}
    session_id = models.UUIDField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['lesson']),
        ]


class ContentSkill(models.Model):
    """Map content/lesson -> skill tag(s)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey('content.Lesson', on_delete=models.CASCADE, related_name='content_skills')
    skill = models.CharField(max_length=128)  # e.g., 'fractions:add'
    weight = models.FloatField(default=1.0)   # optional: weight of skill in lesson

    class Meta:
        unique_together = ('lesson', 'skill')


class UserSkillMastery(models.Model):
    """Track estimated mastery for a user on each skill (0..1)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skill_masteries')
    skill = models.CharField(max_length=128)
    mastery = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'skill')
        indexes = [models.Index(fields=['user', 'skill'])]


class RecommendationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendation_logs')
    lesson = models.ForeignKey('content.Lesson', on_delete=models.CASCADE)
    score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    reason = models.TextField(blank=True)
    source = models.CharField(max_length=32, default='rule')  # 'rule', 'model', 'manual'
    shown_at = models.DateTimeField(auto_now_add=True)
    acted_at = models.DateTimeField(null=True, blank=True)  # when user clicked/started
    accepted = models.BooleanField(null=True)  # user accepted (started/completed)
    feedback = models.JSONField(default=dict)  # e.g., {'outcome': 'correct', 'attempts': 2}

    class Meta:
        ordering = ['-shown_at']
    

