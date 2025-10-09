# assignments/models.py
"""
Django ORM models for the assignments module.
These are thin persistence layers - all business logic lives in domain objects.
"""
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _



class Assignment(models.Model):
    """
    Represents a homework/assessment assignment in the system.
    Teachers create assignments for students to complete.
    """
    
    class AssignmentType(models.TextChoices):
        HOMEWORK = 'homework', _('Homework')
        QUIZ = 'quiz', _('Quiz')
        PROJECT = 'project', _('Project')
        WORKSHEET = 'worksheet', _('Worksheet')
        ESSAY = 'essay', _('Essay')
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    classroom = models.ForeignKey(
        'school.ClassroomModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments',
        help_text=_("The classroom this assignment is assigned to")
    )
    lesson = models.ForeignKey(
        'content.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments',
        help_text=_("The lesson this assignment is linked to")
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_created',
        help_text=_("The teacher who created this assignment")
    )
    
    # Core fields
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    instructions = models.TextField(
        blank=True,
        help_text=_("Detailed instructions for students")
    )
    assignment_type = models.CharField(
        max_length=32,
        choices=AssignmentType.choices,
        default=AssignmentType.HOMEWORK
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    # Grading configuration
    max_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('100.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("Maximum possible score")
    )
    passing_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Minimum score to pass")
    )
    
    # Timing
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Due date for submission")
    )
    available_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When assignment becomes available")
    )
    available_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When assignment is no longer available")
    )
    
    # Settings
    allow_late_submissions = models.BooleanField(default=True)
    late_penalty_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text=_("Percentage penalty per day late")
    )
    max_attempts = models.PositiveIntegerField(
        default=1,
        help_text=_("Maximum number of submission attempts (0 = unlimited)")
    )
    is_group_assignment = models.BooleanField(
        default=False,
        help_text=_("Whether this is a group assignment")
    )
    auto_grade = models.BooleanField(
        default=False,
        help_text=_("Whether to automatically grade submissions")
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Assignment')
        verbose_name_plural = _('Assignments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['classroom', 'status']),
            models.Index(fields=['teacher', 'created_at']),
        ]
    
    def __str__(self):
        return self.title


class AssignmentRubric(models.Model):
    """
    Defines a grading rubric for an assignment.
    A rubric contains multiple criteria, each with levels of achievement.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.OneToOneField(
        Assignment,
        on_delete=models.CASCADE,
        related_name='rubric'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Assignment Rubric')
        verbose_name_plural = _('Assignment Rubrics')
    
    def __str__(self):
        return f"Rubric for {self.assignment.title}"


class RubricCriterion(models.Model):
    """
    Individual criterion in a rubric (e.g., "Grammar", "Content Quality").
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rubric = models.ForeignKey(
        AssignmentRubric,
        on_delete=models.CASCADE,
        related_name='criteria'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    max_points = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('Rubric Criterion')
        verbose_name_plural = _('Rubric Criteria')
        ordering = ['order', 'name']
        unique_together = [['rubric', 'name']]
    
    def __str__(self):
        return self.name


class RubricLevel(models.Model):
    """
    Performance level for a criterion (e.g., "Excellent", "Good", "Poor").
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    criterion = models.ForeignKey(
        RubricCriterion,
        on_delete=models.CASCADE,
        related_name='levels'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    points = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('Rubric Level')
        verbose_name_plural = _('Rubric Levels')
        ordering = ['-points']
        unique_together = [['criterion', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.points} pts)"


class Submission(models.Model):
    """
    Student submission for an assignment.
    Tracks submission state, grade, and feedback.
    """
    
    class SubmissionStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SUBMITTED = 'submitted', _('Submitted')
        LATE = 'late', _('Late')
        GRADING = 'grading', _('Being Graded')
        GRADED = 'graded', _('Graded')
        RETURNED = 'returned', _('Returned to Student')
        RESUBMITTED = 'resubmitted', _('Resubmitted')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    attempt = models.ForeignKey(
        'activities.ExerciseAttempt',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignment_submissions',
        help_text=_("Linked exercise attempt for auto-graded assignments")
    )
    
    # Submission data
    status = models.CharField(
        max_length=32,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.DRAFT,
        db_index=True
    )
    content = models.TextField(
        blank=True,
        help_text=_("Text content of submission")
    )
    attempt_number = models.PositiveIntegerField(default=1)
    
    # Grading
    raw_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    final_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Score after applying penalties/bonuses")
    )
    late_penalty_applied = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Feedback
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions'
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Submission')
        verbose_name_plural = _('Submissions')
        ordering = ['-submitted_at']
        unique_together = [['assignment', 'student', 'attempt_number']]
        indexes = [
            models.Index(fields=['assignment', 'status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['status', 'submitted_at']),
        ]
    
    def __str__(self):
        return f"Submission by {self.student} for {self.assignment.title}"


class SubmissionAttachment(models.Model):
    """
    File attachments for submissions (PDFs, images, documents, etc.).
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='assignments/submissions/%Y/%m/%d/',
        max_length=500
    )
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text=_("Size in bytes"))
    mime_type = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Submission Attachment')
        verbose_name_plural = _('Submission Attachments')
        ordering = ['uploaded_at']
    
    def __str__(self):
        return self.filename


class SubmissionRubricScore(models.Model):
    """
    Stores the score for each rubric criterion in a submission.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='rubric_scores'
    )
    criterion = models.ForeignKey(
        RubricCriterion,
        on_delete=models.CASCADE,
        related_name='scores'
    )
    selected_level = models.ForeignKey(
        RubricLevel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='submissions_scored'
    )
    points_awarded = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    feedback = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Rubric Score')
        verbose_name_plural = _('Rubric Scores')
        unique_together = [['submission', 'criterion']]
    
    def __str__(self):
        return f"{self.criterion.name}: {self.points_awarded} pts"


class AssignmentOverride(models.Model):
    """
    Allows per-student or per-group overrides of assignment settings.
    Useful for accommodations, extensions, etc.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='overrides'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assignment_overrides',
        help_text=_("Specific student (for individual overrides)")
    )
    group = models.ForeignKey(
        'school.ClassroomModel',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assignment_overrides',
        help_text=_("Group (for group overrides)")
    )
    
    # Override fields
    due_date = models.DateTimeField(null=True, blank=True)
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    max_attempts = models.PositiveIntegerField(null=True, blank=True)
    max_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='overrides_created'
    )
    reason = models.TextField(blank=True, help_text=_("Reason for override"))
    
    class Meta:
        verbose_name = _('Assignment Override')
        verbose_name_plural = _('Assignment Overrides')
        indexes = [
            models.Index(fields=['assignment', 'student']),
            models.Index(fields=['assignment', 'group']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(student__isnull=False) | models.Q(group__isnull=False),
                name='override_requires_student_or_group'
            )
        ]
    
    def __str__(self):
        target = self.student or self.group
        return f"Override for {target} on {self.assignment.title}"