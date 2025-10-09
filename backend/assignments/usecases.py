# assignments/usecases.py
"""
Use cases for the assignments module.
These orchestrate domain logic and handle application workflows.
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
import logging

from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError

from .models import (
    Assignment, Submission, AssignmentRubric, RubricCriterion,
    SubmissionRubricScore, SubmissionAttachment, AssignmentOverride
)
from .domain.entities import (
    AssignmentEntity, SubmissionEntity, AssignmentStatus, SubmissionStatus
)
from .domain.value_objects import (
    Score, DueDate, LatePenalty, AttemptsConfig, RubricCriterionScore
)
from .domain.events import AssignmentCreatedEvent, SubmissionCreatedEvent

logger = logging.getLogger(__name__)


class CreateAssignmentUseCase:
    """Use case for creating a new assignment."""
    
    @transaction.atomic
    def execute(
        self,
        teacher_id: str,
        title: str,
        description: str = "",
        instructions: str = "",
        assignment_type: str = "homework",
        classroom_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        max_score: Decimal = Decimal('100.00'),
        passing_score: Optional[Decimal] = None,
        due_date: Optional[datetime] = None,
        available_from: Optional[datetime] = None,
        available_until: Optional[datetime] = None,
        allow_late_submissions: bool = True,
        late_penalty_percent: Decimal = Decimal('10.00'),
        max_attempts: int = 1,
        is_group_assignment: bool = False,
        auto_grade: bool = False
    ) -> AssignmentEntity:
        """
        Create a new assignment.
        
        Args:
            teacher_id: ID of the teacher creating the assignment.
            title: Assignment title.
            description: Assignment description.
            instructions: Detailed instructions.
            assignment_type: Type of assignment (homework, quiz, etc).
            classroom_id: Optional classroom to assign to.
            lesson_id: Optional lesson to link to.
            max_score: Maximum possible score.
            passing_score: Minimum passing score.
            due_date: Due date for submission.
            available_from: When assignment becomes available.
            available_until: When assignment closes.
            allow_late_submissions: Whether to accept late submissions.
            late_penalty_percent: Penalty percentage per day late.
            max_attempts: Maximum submission attempts.
            is_group_assignment: Whether this is a group assignment.
            auto_grade: Whether to auto-grade submissions.
        
        Returns:
            Created AssignmentEntity.
        
        Raises:
            ValidationError: If validation fails.
        """
        # Create due date value object if provided
        due_date_vo = None
        if due_date:
            due_date_vo = DueDate(
                due_at=due_date,
                available_from=available_from,
                available_until=available_until
            )
        
        # Create late penalty value object
        late_penalty = LatePenalty(
            penalty_percent_per_day=late_penalty_percent,
            max_penalty_percent=Decimal('100.00'),
            grace_period_hours=0
        )
        
        # Create attempts config
        attempts_config = AttemptsConfig(
            max_attempts=max_attempts,
            current_attempt=1
        )
        
        # Create domain entity
        entity = AssignmentEntity(
            title=title,
            description=description,
            instructions=instructions,
            assignment_type=assignment_type,
            status=AssignmentStatus.DRAFT,
            classroom_id=classroom_id,
            lesson_id=lesson_id,
            teacher_id=teacher_id,
            max_score=max_score,
            passing_score=passing_score,
            due_date=due_date_vo,
            allow_late_submissions=allow_late_submissions,
            late_penalty=late_penalty,
            attempts_config=attempts_config,
            is_group_assignment=is_group_assignment,
            auto_grade=auto_grade
        )
        
        # Validate
        entity.validate()
        
        # Persist to database
        assignment_model = Assignment.objects.create(
            classroom_id=classroom_id,
            lesson_id=lesson_id,
            teacher_id=teacher_id,
            title=title,
            description=description,
            instructions=instructions,
            assignment_type=assignment_type,
            status=AssignmentStatus.DRAFT.value,
            max_score=max_score,
            passing_score=passing_score,
            due_date=due_date,
            available_from=available_from,
            available_until=available_until,
            allow_late_submissions=allow_late_submissions,
            late_penalty_percent=late_penalty_percent,
            max_attempts=max_attempts,
            is_group_assignment=is_group_assignment,
            auto_grade=auto_grade
        )
        
        entity.id = str(assignment_model.id)
        entity.created_at = assignment_model.created_at
        entity.updated_at = assignment_model.updated_at
        
        # Add event
        entity._add_event(AssignmentCreatedEvent(
            assignment_id=entity.id,
            title=title,
            teacher_id=teacher_id,
            classroom_id=classroom_id,
            occurred_at=datetime.now(timezone.utc)
        ))
        
        logger.info(f"Assignment created: {entity.id} - {title}")
        
        return entity


class PublishAssignmentUseCase:
    """Use case for publishing an assignment."""
    
    @transaction.atomic
    def execute(self, assignment_id: str, teacher_id: str) -> AssignmentEntity:
        """
        Publish an assignment, making it available to students.
        
        Args:
            assignment_id: ID of assignment to publish.
            teacher_id: ID of teacher publishing (for authorization).
        
        Returns:
            Updated AssignmentEntity.
        
        Raises:
            PermissionDenied: If teacher doesn't own the assignment.
            ValidationError: If assignment cannot be published.
        """
        # Load from database
        assignment_model = Assignment.objects.get(id=assignment_id)
        
        # Check authorization
        if str(assignment_model.teacher_id) != teacher_id:
            raise PermissionDenied("Only the assignment creator can publish it")
        
        # Convert to domain entity
        entity = self._model_to_entity(assignment_model)
        
        # Publish (domain logic)
        entity.publish()
        
        # Persist changes
        assignment_model.status = entity.status.value
        assignment_model.updated_at = entity.updated_at
        assignment_model.save(update_fields=['status', 'updated_at'])
        
        logger.info(f"Assignment published: {assignment_id}")
        
        return entity
    
    def _model_to_entity(self, model: Assignment) -> AssignmentEntity:
        """Convert Django model to domain entity."""
        due_date = None
        if model.due_date:
            due_date = DueDate(
                due_at=model.due_date,
                available_from=model.available_from,
                available_until=model.available_until
            )
        
        late_penalty = LatePenalty(
            penalty_percent_per_day=model.late_penalty_percent,
            max_penalty_percent=Decimal('100.00'),
            grace_period_hours=0
        )
        
        attempts_config = AttemptsConfig(
            max_attempts=model.max_attempts,
            current_attempt=1
        )
        
        return AssignmentEntity(
            id=str(model.id),
            title=model.title,
            description=model.description,
            instructions=model.instructions,
            assignment_type=model.assignment_type,
            status=AssignmentStatus(model.status),
            classroom_id=str(model.classroom_id) if model.classroom_id else None,
            lesson_id=str(model.lesson_id) if model.lesson_id else None,
            teacher_id=str(model.teacher_id) if model.teacher_id else None,
            max_score=model.max_score,
            passing_score=model.passing_score,
            due_date=due_date,
            allow_late_submissions=model.allow_late_submissions,
            late_penalty=late_penalty,
            attempts_config=attempts_config,
            is_group_assignment=model.is_group_assignment,
            auto_grade=model.auto_grade,
            created_at=model.created_at,
            updated_at=model.updated_at
        )


class SubmitAssignmentUseCase:
    """Use case for students submitting assignments."""
    
    @transaction.atomic
    def execute(
        self,
        assignment_id: str,
        student_id: str,
        content: str = "",
        file_attachments: Optional[List[Dict[str, Any]]] = None,
        submission_time: Optional[datetime] = None
    ) -> SubmissionEntity:
        """
        Submit an assignment for grading.
        
        Args:
            assignment_id: ID of the assignment.
            student_id: ID of the student submitting.
            content: Text content of submission.
            file_attachments: List of file attachment data.
            submission_time: Time of submission (defaults to now).
        
        Returns:
            SubmissionEntity.
        
        Raises:
            ValidationError: If submission is invalid.
        """
        submission_time = submission_time or datetime.now(timezone.utc)
        
        # Load assignment
        assignment_model = Assignment.objects.get(id=assignment_id)
        assignment_entity = self._model_to_assignment_entity(assignment_model)
        
        # Check if assignment is available
        if not assignment_entity.is_available_for_submission(submission_time):
            raise ValidationError("Assignment is not available for submission")
        
        # Get existing submissions to determine attempt number
        existing_count = Submission.objects.filter(
            assignment_id=assignment_id,
            student_id=student_id
        ).count()
        
        attempt_number = existing_count + 1
        
        # Check attempt limits
        if not assignment_entity.can_submit_attempt(attempt_number):
            raise ValidationError(
                f"Maximum attempts ({assignment_entity.attempts_config.max_attempts}) exceeded"
            )
        
        # Create submission entity
        submission_entity = SubmissionEntity(
            assignment_id=assignment_id,
            student_id=student_id,
            content=content,
            attempt_number=attempt_number,
            status=SubmissionStatus.DRAFT
        )
        
        # Submit (domain logic)
        submission_entity.submit(assignment_entity, submission_time)
        
        # Persist to database
        submission_model = Submission.objects.create(
            assignment_id=assignment_id,
            student_id=student_id,
            content=content,
            attempt_number=attempt_number,
            status=submission_entity.status.value,
            submitted_at=submission_entity.submitted_at
        )
        
        submission_entity.id = str(submission_model.id)
        submission_entity.created_at = submission_model.created_at
        submission_entity.updated_at = submission_model.updated_at
        
        # Handle file attachments
        if file_attachments:
            for attachment_data in file_attachments:
                SubmissionAttachment.objects.create(
                    submission=submission_model,
                    file=attachment_data['file'],
                    filename=attachment_data['filename'],
                    file_size=attachment_data['file_size'],
                    mime_type=attachment_data.get('mime_type', '')
                )
        
        logger.info(
            f"Submission created: {submission_entity.id} "
            f"(assignment: {assignment_id}, student: {student_id}, "
            f"attempt: {attempt_number})"
        )
        
        return submission_entity
    
    def _model_to_assignment_entity(self, model: Assignment) -> AssignmentEntity:
        """Convert model to entity."""
        due_date = None
        if model.due_date:
            due_date = DueDate(
                due_at=model.due_date,
                available_from=model.available_from,
                available_until=model.available_until
            )
        
        late_penalty = LatePenalty(
            penalty_percent_per_day=model.late_penalty_percent
        )
        
        attempts_config = AttemptsConfig(max_attempts=model.max_attempts)
        
        return AssignmentEntity(
            id=str(model.id),
            title=model.title,
            teacher_id=str(model.teacher_id) if model.teacher_id else None,
            max_score=model.max_score,
            passing_score=model.passing_score,
            due_date=due_date,
            allow_late_submissions=model.allow_late_submissions,
            late_penalty=late_penalty,
            attempts_config=attempts_config,
            status=AssignmentStatus(model.status)
        )


class GradeSubmissionUseCase:
    """Use case for grading a submission."""
    
    @transaction.atomic
    def execute(
        self,
        submission_id: str,
        grader_id: str,
        raw_score_value: Decimal,
        feedback: str = "",
        rubric_scores: Optional[List[Dict[str, Any]]] = None
    ) -> SubmissionEntity:
        """
        Grade a student submission.
        
        Args:
            submission_id: ID of the submission to grade.
            grader_id: ID of the person grading.
            raw_score_value: The raw score before penalties.
            feedback: Grading feedback text.
            rubric_scores: Optional list of rubric criterion scores.
        
        Returns:
            Updated SubmissionEntity.
        
        Raises:
            ValidationError: If grading is invalid.
        """
        # Load submission
        submission_model = Submission.objects.select_related('assignment').get(
            id=submission_id
        )
        assignment_model = submission_model.assignment
        
        # Convert to entities
        assignment_entity = self._model_to_assignment_entity(assignment_model)
        submission_entity = self._model_to_submission_entity(submission_model)
        
        # Create score value object
        raw_score = Score(
            value=raw_score_value,
            max_value=assignment_entity.max_score
        )
        
        # Convert rubric scores if provided
        rubric_score_vos = None
        if rubric_scores:
            rubric_score_vos = [
                RubricCriterionScore(
                    criterion_id=rs['criterion_id'],
                    criterion_name=rs['criterion_name'],
                    max_points=Decimal(str(rs['max_points'])),
                    points_awarded=Decimal(str(rs['points_awarded'])),
                    level_name=rs.get('level_name'),
                    feedback=rs.get('feedback', '')
                )
                for rs in rubric_scores
            ]
        
        # Apply grade (domain logic)
        submission_entity.apply_grade(
            raw_score=raw_score,
            assignment=assignment_entity,
            grader_id=grader_id,
            feedback=feedback,
            rubric_scores=rubric_score_vos
        )
        
        # Persist changes
        submission_model.status = submission_entity.status.value
        submission_model.raw_score = submission_entity.raw_score.value
        submission_model.final_score = submission_entity.final_score.value
        submission_model.late_penalty_applied = submission_entity.late_penalty_applied
        submission_model.feedback = feedback
        submission_model.graded_by_id = grader_id
        submission_model.graded_at = submission_entity.graded_at
        submission_model.updated_at = submission_entity.updated_at
        submission_model.save()
        
        # Save rubric scores if provided
        if rubric_score_vos:
            for rs_vo in rubric_score_vos:
                criterion = RubricCriterion.objects.get(id=rs_vo.criterion_id)
                SubmissionRubricScore.objects.create(
                    submission=submission_model,
                    criterion=criterion,
                    points_awarded=rs_vo.points_awarded,
                    feedback=rs_vo.feedback
                )
        
        logger.info(
            f"Submission graded: {submission_id} - "
            f"Raw: {raw_score.value}, Final: {submission_entity.final_score.value}"
        )
        
        return submission_entity
    
    def _model_to_assignment_entity(self, model: Assignment) -> AssignmentEntity:
        """Convert model to entity."""
        due_date = None
        if model.due_date:
            due_date = DueDate(
                due_at=model.due_date,
                available_from=model.available_from,
                available_until=model.available_until
            )
        
        late_penalty = LatePenalty(
            penalty_percent_per_day=model.late_penalty_percent
        )
        
        return AssignmentEntity(
            id=str(model.id),
            title=model.title,
            max_score=model.max_score,
            passing_score=model.passing_score,
            due_date=due_date,
            late_penalty=late_penalty
        )
    
    def _model_to_submission_entity(self, model: Submission) -> SubmissionEntity:
        """Convert model to entity."""
        return SubmissionEntity(
            id=str(model.id),
            assignment_id=str(model.assignment_id),
            student_id=str(model.student_id),
            status=SubmissionStatus(model.status),
            content=model.content,
            attempt_number=model.attempt_number,
            submitted_at=model.submitted_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )


class CalculateFinalScoreUseCase:
    """Use case for calculating final scores with overrides and penalties."""
    
    def execute(
        self,
        assignment_id: str,
        student_id: str,
        raw_score: Decimal,
        submission_time: datetime
    ) -> Dict[str, Any]:
        """
        Calculate the final score for a submission.
        
        Args:
            assignment_id: ID of the assignment.
            student_id: ID of the student.
            raw_score: Raw score before penalties.
            submission_time: When the submission was made.
        
        Returns:
            Dictionary with final score details.
        """
        # Load assignment
        assignment = Assignment.objects.get(id=assignment_id)
        
        # Check for overrides
        override = AssignmentOverride.objects.filter(
            assignment_id=assignment_id,
            student_id=student_id
        ).first()
        
        # Use override due date if exists
        due_date_value = override.due_date if override and override.due_date else assignment.due_date
        
        if not due_date_value:
            # No due date, no penalty
            return {
                'raw_score': float(raw_score),
                'final_score': float(raw_score),
                'penalty_percent': 0.0,
                'is_late': False,
                'days_late': 0
            }
        
        # Create domain objects
        due_date = DueDate(
            due_at=due_date_value,
            available_from=assignment.available_from,
            available_until=assignment.available_until
        )
        
        late_penalty = LatePenalty(
            penalty_percent_per_day=assignment.late_penalty_percent
        )
        
        score = Score(value=raw_score, max_value=assignment.max_score)
        
        # Calculate penalty
        is_late = due_date.is_past_due(submission_time)
        penalty_percent = late_penalty.calculate_penalty(due_date, submission_time) if is_late else Decimal('0.00')
        final_score = late_penalty.apply_to_score(score, due_date, submission_time)
        
        return {
            'raw_score': float(score.value),
            'final_score': float(final_score.value),
            'penalty_percent': float(penalty_percent),
            'is_late': is_late,
            'days_late': due_date.days_late(submission_time) if is_late else 0
        }


class BulkGradeSubmissionsUseCase:
    """Use case for bulk grading multiple submissions."""
    
    @transaction.atomic
    def execute(
        self,
        assignment_id: str,
        grader_id: str,
        grades: List[Dict[str, Any]]
    ) -> List[SubmissionEntity]:
        """
        Grade multiple submissions at once.
        
        Args:
            assignment_id: ID of the assignment.
            grader_id: ID of the grader.
            grades: List of dictionaries with submission_id and score.
        
        Returns:
            List of graded SubmissionEntity objects.
        """
        graded_submissions = []
        grade_usecase = GradeSubmissionUseCase()
        
        for grade_data in grades:
            try:
                submission = grade_usecase.execute(
                    submission_id=grade_data['submission_id'],
                    grader_id=grader_id,
                    raw_score_value=Decimal(str(grade_data['score'])),
                    feedback=grade_data.get('feedback', ''),
                    rubric_scores=grade_data.get('rubric_scores')
                )
                graded_submissions.append(submission)
            except Exception as e:
                logger.error(
                    f"Error grading submission {grade_data['submission_id']}: {e}"
                )
                # Continue with other submissions
        
        logger.info(
            f"Bulk graded {len(graded_submissions)} submissions "
            f"for assignment {assignment_id}"
        )
        
        return graded_submissions


class GetStudentAssignmentsUseCase:
    """Use case for retrieving student assignments."""
    
    def execute(
        self,
        student_id: str,
        classroom_id: Optional[str] = None,
        status: Optional[str] = None,
        include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get assignments for a student.
        
        Args:
            student_id: ID of the student.
            classroom_id: Optional filter by classroom.
            status: Optional filter by status.
            include_archived: Whether to include archived assignments.
        
        Returns:
            List of assignment dictionaries with submission status.
        """
        # Build query
        query = Assignment.objects.filter(status=AssignmentStatus.PUBLISHED.value)
        
        if classroom_id:
            query = query.filter(classroom_id=classroom_id)
        
        if not include_archived:
            query = query.exclude(status=AssignmentStatus.ARCHIVED.value)
        
        assignments = []
        for assignment in query.order_by('-due_date'):
            # Get student's submissions for this assignment
            submissions = Submission.objects.filter(
                assignment_id=assignment.id,
                student_id=student_id
            ).order_by('-attempt_number')
            
            latest_submission = submissions.first()
            
            assignment_data = {
                'id': str(assignment.id),
                'title': assignment.title,
                'description': assignment.description,
                'assignment_type': assignment.assignment_type,
                'max_score': float(assignment.max_score),
                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                'status': assignment.status,
                'attempts_used': submissions.count(),
                'max_attempts': assignment.max_attempts,
                'has_submission': latest_submission is not None,
                'submission_status': latest_submission.status if latest_submission else None,
                'final_score': float(latest_submission.final_score) if latest_submission and latest_submission.final_score else None
            }
            
            assignments.append(assignment_data)
        
        return assignments


class CreateRubricUseCase:
    """Use case for creating assignment rubrics."""
    
    @transaction.atomic
    def execute(
        self,
        assignment_id: str,
        title: str,
        description: str = "",
        criteria: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a grading rubric for an assignment.
        
        Args:
            assignment_id: ID of the assignment.
            title: Rubric title.
            description: Rubric description.
            criteria: List of criteria with levels.
        
        Returns:
            Dictionary representation of the rubric.
        """
        assignment = Assignment.objects.get(id=assignment_id)
        
        # Create rubric
        rubric = AssignmentRubric.objects.create(
            assignment=assignment,
            title=title,
            description=description
        )
        
        # Create criteria and levels
        created_criteria = []
        for i, criterion_data in enumerate(criteria or []):
            criterion = RubricCriterion.objects.create(
                rubric=rubric,
                name=criterion_data['name'],
                description=criterion_data.get('description', ''),
                max_points=Decimal(str(criterion_data['max_points'])),
                order=i
            )
            
            created_levels = []
            for level_data in criterion_data.get('levels', []):
                level = criterion.levels.create(
                    name=level_data['name'],
                    description=level_data.get('description', ''),
                    points=Decimal(str(level_data['points'])),
                    order=level_data.get('order', 0)
                )
                created_levels.append({
                    'id': str(level.id),
                    'name': level.name,
                    'points': float(level.points)
                })
            
            created_criteria.append({
                'id': str(criterion.id),
                'name': criterion.name,
                'max_points': float(criterion.max_points),
                'levels': created_levels
            })
        
        logger.info(f"Rubric created for assignment {assignment_id}")
        
        return {
            'id': str(rubric.id),
            'title': rubric.title,
            'description': rubric.description,
            'criteria': created_criteria
        }