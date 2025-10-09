# assignments/admin.py
"""
Django admin configuration for the assignments module.
Provides a user-friendly interface for managing assignments, submissions, and rubrics.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from assignments.models import (
    Assignment, Submission, AssignmentRubric, RubricCriterion,
    RubricLevel, SubmissionRubricScore, SubmissionAttachment,
    AssignmentOverride
)


class RubricLevelInline(admin.TabularInline):
    """Inline for rubric levels within a criterion."""
    model = RubricLevel
    extra = 1
    fields = ('name', 'points', 'description', 'order')
    ordering = ['-points']


class RubricCriterionInline(admin.StackedInline):
    """Inline for rubric criteria within a rubric."""
    model = RubricCriterion
    extra = 1
    fields = ('name', 'description', 'max_points', 'order')
    ordering = ['order']


class SubmissionAttachmentInline(admin.TabularInline):
    """Inline for submission attachments."""
    model = SubmissionAttachment
    extra = 0
    readonly_fields = ('filename', 'file_size', 'mime_type', 'uploaded_at')
    fields = ('file', 'filename', 'file_size', 'mime_type', 'uploaded_at')
    can_delete = True


class SubmissionRubricScoreInline(admin.TabularInline):
    """Inline for rubric scores within a submission."""
    model = SubmissionRubricScore
    extra = 0
    fields = ('criterion', 'selected_level', 'points_awarded', 'feedback')
    readonly_fields = ('criterion',)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """Admin interface for assignments."""
    
    list_display = (
        'title', 'assignment_type', 'status', 'teacher_link',
        'classroom_link', 'due_date_display', 'max_score',
        'submission_count', 'created_at'
    )
    list_filter = (
        'status', 'assignment_type', 'is_group_assignment',
        'auto_grade', 'allow_late_submissions', 'created_at'
    )
    search_fields = ('title', 'description', 'teacher__username')
    readonly_fields = ('id', 'created_at', 'updated_at', 'submission_count')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'id', 'title', 'description', 'instructions',
                'assignment_type', 'status'
            )
        }),
        (_('Relationships'), {
            'fields': ('classroom', 'lesson', 'teacher')
        }),
        (_('Grading Configuration'), {
            'fields': (
                'max_score', 'passing_score', 'auto_grade'
            )
        }),
        (_('Timing'), {
            'fields': (
                'due_date', 'available_from', 'available_until'
            )
        }),
        (_('Submission Settings'), {
            'fields': (
                'max_attempts', 'is_group_assignment',
                'allow_late_submissions', 'late_penalty_percent'
            )
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at', 'submission_count'),
            'classes': ('collapse',)
        })
    )
    
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def teacher_link(self, obj):
        """Link to teacher's admin page."""
        if obj.teacher:
            url = reverse('admin:auth_user_change', args=[obj.teacher.id])
            return format_html('<a href="{}">{}</a>', url, obj.teacher.username)
        return '-'
    teacher_link.short_description = _('Teacher')
    
    def classroom_link(self, obj):
        """Link to classroom's admin page."""
        if obj.classroom:
            url = reverse('admin:school_classroommodel_change', args=[obj.classroom.id])
            return format_html('<a href="{}">{}</a>', url, str(obj.classroom))
        return '-'
    classroom_link.short_description = _('Classroom')
    
    def due_date_display(self, obj):
        """Formatted due date display."""
        if obj.due_date:
            return obj.due_date.strftime('%Y-%m-%d %H:%M')
        return '-'
    due_date_display.short_description = _('Due Date')
    
    def submission_count(self, obj):
        """Count of submissions for this assignment."""
        return obj.submissions.count()
    submission_count.short_description = _('Submissions')
    
    actions = ['publish_assignments', 'archive_assignments']
    
    def publish_assignments(self, request, queryset):
        """Bulk publish assignments."""
        updated = queryset.filter(status='draft').update(status='published')
        self.message_user(
            request,
            f'{updated} assignment(s) published successfully.'
        )
    publish_assignments.short_description = _('Publish selected assignments')
    
    def archive_assignments(self, request, queryset):
        """Bulk archive assignments."""
        updated = queryset.update(status='archived')
        self.message_user(
            request,
            f'{updated} assignment(s) archived successfully.'
        )
    archive_assignments.short_description = _('Archive selected assignments')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Admin interface for submissions."""
    
    list_display = (
        'id_short', 'assignment_link', 'student_link', 'status',
        'attempt_number', 'score_display', 'submitted_at', 'is_late'
    )
    list_filter = (
        'status', 'submitted_at', 'graded_at'
    )
    search_fields = (
        'student__username', 'assignment__title', 'feedback'
    )
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'submitted_at',
        'graded_at', 'late_penalty_applied'
    )
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'id', 'assignment', 'student', 'attempt',
                'attempt_number', 'status'
            )
        }),
        (_('Content'), {
            'fields': ('content',)
        }),
        (_('Grading'), {
            'fields': (
                'raw_score', 'final_score', 'late_penalty_applied',
                'graded_by', 'graded_at', 'feedback'
            )
        }),
        (_('Timestamps'), {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [SubmissionAttachmentInline, SubmissionRubricScoreInline]
    
    date_hierarchy = 'submitted_at'
    ordering = ('-submitted_at',)
    
    def id_short(self, obj):
        """Shortened UUID display."""
        return str(obj.id)[:8]
    id_short.short_description = _('ID')
    
    def assignment_link(self, obj):
        """Link to assignment."""
        url = reverse('admin:assignments_assignment_change', args=[obj.assignment.id])
        return format_html('<a href="{}">{}</a>', url, obj.assignment.title)
    assignment_link.short_description = _('Assignment')
    
    def student_link(self, obj):
        """Link to student."""
        if obj.student:
            url = reverse('admin:auth_user_change', args=[obj.student.id])
            return format_html('<a href="{}">{}</a>', url, obj.student.username)
        return '-'
    student_link.short_description = _('Student')
    
    def score_display(self, obj):
        """Display score with color coding."""
        if obj.final_score is None:
            return '-'
        
        percentage = (obj.final_score / obj.assignment.max_score * 100) if obj.assignment.max_score else 0
        
        if percentage >= 90:
            color = 'green'
        elif percentage >= 70:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}/{:.1f}</span>',
            color, obj.final_score, obj.assignment.max_score
        )
    score_display.short_description = _('Score')
    
    def is_late(self, obj):
        """Display if submission is late."""
        return obj.status == 'late'
    is_late.boolean = True
    is_late.short_description = _('Late')


@admin.register(AssignmentRubric)
class AssignmentRubricAdmin(admin.ModelAdmin):
    """Admin interface for rubrics."""
    
    list_display = ('title', 'assignment_link', 'criteria_count', 'created_at')
    search_fields = ('title', 'description', 'assignment__title')
    readonly_fields = ('id', 'created_at', 'updated_at', 'criteria_count')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'assignment', 'title', 'description')
        }),
        (_('Metadata'), {
            'fields': ('criteria_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [RubricCriterionInline]
    
    def assignment_link(self, obj):
        """Link to assignment."""
        url = reverse('admin:assignments_assignment_change', args=[obj.assignment.id])
        return format_html('<a href="{}">{}</a>', url, obj.assignment.title)
    assignment_link.short_description = _('Assignment')
    
    def criteria_count(self, obj):
        """Count of criteria in rubric."""
        return obj.criteria.count()
    criteria_count.short_description = _('Criteria Count')


@admin.register(RubricCriterion)
class RubricCriterionAdmin(admin.ModelAdmin):
    """Admin interface for rubric criteria."""
    
    list_display = ('name', 'rubric', 'max_points', 'order', 'levels_count')
    list_filter = ('rubric__assignment__assignment_type',)
    search_fields = ('name', 'description', 'rubric__title')
    readonly_fields = ('id', 'levels_count')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'rubric', 'name', 'description')
        }),
        (_('Configuration'), {
            'fields': ('max_points', 'order')
        })
    )
    
    inlines = [RubricLevelInline]
    ordering = ['rubric', 'order']
    
    def levels_count(self, obj):
        """Count of performance levels."""
        return obj.levels.count()
    levels_count.short_description = _('Levels')


@admin.register(RubricLevel)
class RubricLevelAdmin(admin.ModelAdmin):
    """Admin interface for rubric levels."""
    
    list_display = ('name', 'criterion', 'points', 'order')
    list_filter = ('criterion__rubric__assignment__assignment_type',)
    search_fields = ('name', 'description', 'criterion__name')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('criterion', 'name', 'description')
        }),
        (_('Configuration'), {
            'fields': ('points', 'order')
        })
    )
    
    ordering = ['criterion', '-points']


@admin.register(AssignmentOverride)
class AssignmentOverrideAdmin(admin.ModelAdmin):
    """Admin interface for assignment overrides."""
    
    list_display = (
        'assignment_link', 'target_display', 'due_date',
        'max_attempts', 'created_by_link', 'created_at'
    )
    list_filter = ('created_at',)
    search_fields = (
        'assignment__title', 'student__username',
        'reason'
    )
    readonly_fields = ('id', 'created_at')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('id', 'assignment', 'student', 'group', 'reason')
        }),
        (_('Overrides'), {
            'fields': (
                'due_date', 'available_from', 'available_until',
                'max_attempts', 'max_score'
            )
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def assignment_link(self, obj):
        """Link to assignment."""
        url = reverse('admin:assignments_assignment_change', args=[obj.assignment.id])
        return format_html('<a href="{}">{}</a>', url, obj.assignment.title)
    assignment_link.short_description = _('Assignment')
    
    def target_display(self, obj):
        """Display student or group."""
        if obj.student:
            return f'Student: {obj.student.username}'
        elif obj.group:
            return f'Group: {obj.group}'
        return '-'
    target_display.short_description = _('Target')
    
    def created_by_link(self, obj):
        """Link to creator."""
        if obj.created_by:
            url = reverse('admin:auth_user_change', args=[obj.created_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.created_by.username)
        return '-'
    created_by_link.short_description = _('Created By')


# Register remaining models with simple admin
admin.site.register(SubmissionAttachment)
admin.site.register(SubmissionRubricScore)
