"""
Mappers for converting between Django models and domain entities.
Implements the Data Mapper pattern to keep domain layer independent of ORM.
"""
from decimal import Decimal
from typing import Optional, List

from assignments.models import (
    Assignment, Submission, SubmissionRubricScore as SubmissionRubricScoreModel,
    RubricCriterion
)
from ..entities import (
    AssignmentEntity, SubmissionEntity, AssignmentStatus, SubmissionStatus
)
from ..value_objects import (
    Score, DueDate, LatePenalty, AttemptsConfig, RubricCriterionScore
)



class AssignmentMapper:
    """Maps between Assignment model and AssignmentEntity."""
    
    @staticmethod
    def to_entity(model: Assignment) -> AssignmentEntity:
        """
        Convert Django model to domain entity.
        
        Args:
            model: Assignment Django model instance.
        
        Returns:
            AssignmentEntity domain object.
        """
        # Build due date value object if exists
        due_date = None
        if model.due_date:
            due_date = DueDate(
                due_at=model.due_date,
                available_from=model.available_from,
                available_until=model.available_until
            )
        
        # Build late penalty value object
        late_penalty = LatePenalty(
            penalty_percent_per_day=model.late_penalty_percent,
            max_penalty_percent=Decimal('100.00'),
            grace_period_hours=0  # Could be added to model if needed
        )
        
        # Build attempts config
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
    
    @staticmethod
    def to_model(entity: AssignmentEntity) -> Assignment:
        """
        Convert domain entity to Django model.
        Note: This creates a new model instance. For updates, use update_model.
        
        Args:
            entity: AssignmentEntity domain object.
        
        Returns:
            Assignment Django model instance (not saved).
        """
        model = Assignment(
            title=entity.title,
            description=entity.description,
            instructions=entity.instructions,
            assignment_type=entity.assignment_type.value if hasattr(entity.assignment_type, 'value') else entity.assignment_type,
            status=entity.status.value,
            classroom_id=entity.classroom_id,
            lesson_id=entity.lesson_id,
            teacher_id=entity.teacher_id,
            max_score=entity.max_score,
            passing_score=entity.passing_score,
            due_date=entity.due_date.due_at if entity.due_date else None,
            available_from=entity.due_date.available_from if entity.due_date else None,
            available_until=entity.due_date.available_until if entity.due_date else None,
            allow_late_submissions=entity.allow_late_submissions,
            late_penalty_percent=entity.late_penalty.penalty_percent_per_day,
            max_attempts=entity.attempts_config.max_attempts,
            is_group_assignment=entity.is_group_assignment,
            auto_grade=entity.auto_grade
        )
        
        if entity.id:
            model.id = entity.id
        
        return model
    
    @staticmethod
    def update_model(model: Assignment, entity: AssignmentEntity) -> Assignment:
        """
        Update existing Django model from entity.
        
        Args:
            model: Existing Assignment model to update.
            entity: AssignmentEntity with updated data.
        
        Returns:
            Updated Assignment model (not saved).
        """
        model.title = entity.title
        model.description = entity.description
        model.instructions = entity.instructions
        model.assignment_type = entity.assignment_type.value if hasattr(entity.assignment_type, 'value') else entity.assignment_type
        model.status = entity.status.value
        model.classroom_id = entity.classroom_id
        model.lesson_id = entity.lesson_id
        model.teacher_id = entity.teacher_id
        model.max_score = entity.max_score
        model.passing_score = entity.passing_score
        
        if entity.due_date:
            model.due_date = entity.due_date.due_at
            model.available_from = entity.due_date.available_from
            model.available_until = entity.due_date.available_until
        else:
            model.due_date = None
            model.available_from = None
            model.available_until = None
        
        model.allow_late_submissions = entity.allow_late_submissions
        model.late_penalty_percent = entity.late_penalty.penalty_percent_per_day
        model.max_attempts = entity.attempts_config.max_attempts
        model.is_group_assignment = entity.is_group_assignment
        model.auto_grade = entity.auto_grade
        
        return model