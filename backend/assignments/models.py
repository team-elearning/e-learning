import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from activities.models import ExerciseAttempt



# Create your models here.
class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey('school.ClassroomModel', on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments')
    lesson = models.ForeignKey('content.Lesson', on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments_given')
    title = models.CharField(max_length=255)
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = ('Assignment')
        verbose_name_plural = ('Assignments')

    def __str__(self):
        return self.title

class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='submissions')
    attempt = models.ForeignKey(ExerciseAttempt, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=32,
        default='submitted',
        choices=[('submitted', ('Submitted')), ('graded', ('Graded')), ('late', ('Late'))]
    )
    grade = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = ('Submission')
        verbose_name_plural = ('Submissions')

    def __str__(self):
        return f"Submission for {self.assignment} by {self.student}"