# assignments/domain/factories/assignment_factory.py
"""
Factory classes for creating domain entities with validation.
Follows the Factory pattern for complex object creation.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
import logging

from ..entities import AssignmentEntity, SubmissionEntity, AssignmentStatus, SubmissionStatus
from ..value_objects import DueDate, LatePenalty, AttemptsConfig

logger = logging.getLogger(__name__)

class AssignmentFactory:
    """
    Factory for creating AssignmentEntity objects with proper validation.
    Encapsulates the complexity of creating assignments with all their dependencies.
    """
    
    @staticmethod
    def create(
        title: str,
        teacher_id: str,
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
        late_penalty_percent_per_day: Decimal = Decimal('10.00'),
        late_penalty_grace_period_hours: int = 0,
        max_attempts: int = 1,
        is_group_assignment: bool = False,
        auto_grade: bool = False
    ) -> AssignmentEntity:
        """
        Create a new assignment entity with full validation.
        
        Args:
            title: Assignment title (required).
            teacher_id: ID of the teacher creating the assignment (required).
            description: Assignment description.
            instructions: Detailed student instructions.
            assignment_type: Type of assignment (homework, quiz, etc).
            classroom_id: Optional classroom ID.
            lesson_id: Optional lesson ID.
            max_score: Maximum possible score.
            passing_score: Minimum passing score.
            due_date: Due date for submission.
            available_from: When assignment becomes available.
            available_until: When assignment closes.
            allow_late_submissions: Whether to accept late submissions.
            late_penalty_percent_per_day: Penalty per day late.
            late_penalty_grace_period_hours: Grace period before penalties apply.
            max_attempts: Maximum submission attempts (0 for unlimited).
            is_group_assignment: Whether this is a group assignment.
            auto_grade: Whether to automatically grade submissions.
        
        Returns:
            Validated AssignmentEntity.
        
        Raises:
            ValueError: If validation fails.
        """
        # Validate inputs
        if not title or not title.strip():
            raise ValueError("Assignment title is required")
        
        if len(title) > 255:
            raise ValueError("Assignment title cannot exceed 255 characters")
        
        if not teacher_id:
            raise ValueError("Teacher ID is required")
        
        if max_score <= Decimal('0'):
            raise ValueError("Max score must be positive")
        
        if passing_score and passing_score > max_score:
            raise ValueError("Passing score cannot exceed max score")
        
        # Create due date value object if provided
        due_date_vo = None
        if due_date:
            # Ensure timezone awareness
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            
            if available_from and available_from.tzinfo is None:
                available_from = available_from.replace(tzinfo=timezone.utc)
            
            if available_until and available_until.tzinfo is None:
                available_until = available_until.replace(tzinfo=timezone.utc)
            
            due_date_vo = DueDate(
                due_at=due_date,
                available_from=available_from,
                available_until=available_until
            )
        
        # Create late penalty value object
        late_penalty = LatePenalty(
            penalty_percent_per_day=late_penalty_percent_per_day,
            max_penalty_percent=Decimal('100.00'),
            grace_period_hours=late_penalty_grace_period_hours
        )
        
        # Create attempts config
        attempts_config = AttemptsConfig(
            max_attempts=max_attempts,
            current_attempt=1
        )
        
        # Create entity
        entity = AssignmentEntity(
            title=title.strip(),
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
            auto_grade=auto_grade,
            created_at=datetime.now(timezone.utc)
        )
        
        # Validate the complete entity
        entity.validate()
        
        logger.info(f"AssignmentFactory created assignment: {title}")
        
        return entity
    
    @staticmethod
    def create_quiz(
        title: str,
        teacher_id: str,
        time_limit_minutes: int = 60,
        **kwargs
    ) -> AssignmentEntity:
        """
        Convenience method for creating quiz assignments.
        
        Args:
            title: Quiz title.
            teacher_id: Teacher ID.
            time_limit_minutes: Time limit for quiz.
            **kwargs: Additional assignment parameters.
        
        Returns:
            AssignmentEntity configured as a quiz.
        """
        # Quizzes typically don't allow late submissions and have 1 attempt
        kwargs.setdefault('assignment_type', 'quiz')
        kwargs.setdefault('allow_late_submissions', False)
        kwargs.setdefault('max_attempts', 1)
        kwargs.setdefault('auto_grade', True)
        
        return AssignmentFactory.create(
            title=title,
            teacher_id=teacher_id,
            **kwargs
        )
    
    @staticmethod
    def create_homework(
        title: str,
        teacher_id: str,
        due_days_from_now: int = 7,
        **kwargs
    ) -> AssignmentEntity:
        """
        Convenience method for creating homework assignments.
        
        Args:
            title: Homework title.
            teacher_id: Teacher ID.
            due_days_from_now: Days until due date.
            **kwargs: Additional assignment parameters.
        
        Returns:
            AssignmentEntity configured as homework.
        """
        # Set due date if not provided
        if 'due_date' not in kwargs:
            kwargs['due_date'] = datetime.now(timezone.utc) + timedelta(days=due_days_from_now)
        
        # Homework typically allows late submissions and multiple attempts
        kwargs.setdefault('assignment_type', 'homework')
        kwargs.setdefault('allow_late_submissions', True)
        kwargs.setdefault('max_attempts', 3)
        kwargs.setdefault('late_penalty_percent_per_day', Decimal('10.00'))
        
        return AssignmentFactory.create(
            title=title,
            teacher_id=teacher_id,
            **kwargs
        )