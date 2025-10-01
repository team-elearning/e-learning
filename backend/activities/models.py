import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class Exercise(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey('content.Lesson', on_delete=models.CASCADE, related_name='exercises')
    title = models.CharField(max_length=255)
    type = models.CharField(
        max_length=32,
        choices=[('mcq', ('Multiple Choice')), ('short_answer', ('Short Answer')), ('matching', ('Matching'))]
    )

    class Meta:
        verbose_name = ('Exercise')
        verbose_name_plural = ('Exercises')

    def __str__(self):
        return self.title

class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='questions')
    prompt = models.TextField()
    meta = models.JSONField(default=dict)  # e.g., {'difficulty': 1-5, 'time_limit': 60, 'hints': [...]}

    class Meta:
        verbose_name = ('Question')
        verbose_name_plural = ('Questions')

    def __str__(self):
        return self.prompt[:50]

class Choice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    position = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = ('Choice')
        verbose_name_plural = ('Choices')
        ordering = ['position']

    def __str__(self):
        return self.text[:50]

class ExerciseAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='exercise_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    metadata = models.JSONField(default=dict)  # e.g., {'time_taken': 300}

    class Meta:
        verbose_name = ('Exercise Attempt')
        verbose_name_plural = ('Exercise Attempts')

    def __str__(self):
        return f"Attempt for {self.exercise} by {self.student}"

class ExerciseAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(ExerciseAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.JSONField(default=dict)  # e.g., {'text': '...', 'selected_choice': 'uuid'}
    correct = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = ('Exercise Answer')
        verbose_name_plural = ('Exercise Answers')

    def __str__(self):
        return f"Answer for {self.question}"
    

class ExerciseSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercise = models.OneToOneField('Exercise', on_delete=models.CASCADE, related_name='settings')
    time_limit_seconds = models.IntegerField(null=True, blank=True)  # None => no limit
    max_attempts = models.IntegerField(null=True, blank=True)  # None => unlimited
    shuffle_questions = models.BooleanField(default=True)
    shuffle_choices = models.BooleanField(default=True)
    pass_score = models.FloatField(default=50.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    negative_marking = models.BooleanField(default=False)  # penalize wrong answers
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Hint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='hints')
    text = models.TextField()
    order = models.IntegerField(default=0)

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True)

class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)

class QuestionStat(models.Model):
    question = models.OneToOneField('Question', on_delete=models.CASCADE, related_name='stats')
    times_shown = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    average_time_seconds = models.FloatField(default=0.0)

class MatchingPair(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='matching_pairs')
    left_text = models.TextField()
    right_text = models.TextField()
    correct_right_index = models.IntegerField()  # index into the right list to mark correct pairing

class FileUploadAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt_answer = models.OneToOneField('ExerciseAnswer', on_delete=models.CASCADE, related_name='file_upload')
    file = models.FileField(upload_to='exercise_answers/')