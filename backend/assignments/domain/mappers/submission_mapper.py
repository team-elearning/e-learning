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



class SubmissionMapper:
    """Maps between Submission model and SubmissionEntity."""
    
    @staticmethod
    def to_entity(
        model: Submission,
        include_rubric_scores: bool = False
    ) -> SubmissionEntity:
        """
        Convert Django model to domain entity.
        
        Args:
            model: Submission Django model instance.
            include_rubric_scores: Whether to load rubric scores.
        
        Returns:
            SubmissionEntity domain object.
        """
        # Build score value objects if they exist
        raw_score = None
        if model.raw_score is not None:
            raw_score = Score(
                value=model.raw_score,
                max_value=model.assignment.max_score
            )
        
        final_score = None
        if model.final_score is not None:
            final_score = Score(
                value=model.final_score,
                max_value=model.assignment.max_score
            )
        
        # Load rubric scores if requested
        rubric_scores = []
        if include_rubric_scores:
            rubric_score_models = model.rubric_scores.select_related('criterion').all()
            for rs_model in rubric_score_models:
                rubric_scores.append(RubricCriterionScore(
                    criterion_id=str(rs_model.criterion.id),
                    criterion_name=rs_model.criterion.name,
                    max_points=rs_model.criterion.max_points,
                    points_awarded=rs_model.points_awarded,
                    level_name=rs_model.selected_level.name if rs_model.selected_level else None,
                    feedback=rs_model.feedback
                ))
        
        return SubmissionEntity(
            id=str(model.id),
            assignment_id=str(model.assignment_id),
            student_id=str(model.student_id),
            attempt_id=str(model.attempt_id) if model.attempt_id else None,
            status=SubmissionStatus(model.status),
            content=model.content,
            attempt_number=model.attempt_number,
            raw_score=raw_score,
            final_score=final_score,
            late_penalty_applied=model.late_penalty_applied,
            rubric_scores=rubric_scores,
            feedback=model.feedback,
            graded_by=str(model.graded_by_id) if model.graded_by_id else None,
            graded_at=model.graded_at,
            submitted_at=model.submitted_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    @staticmethod
    def to_model(entity: SubmissionEntity) -> Submission:
        """
        Convert domain entity to Django model.
        Note: This creates a new model instance. For updates, use update_model.
        
        Args:
            entity: SubmissionEntity domain object.
        
        Returns:
            Submission Django model instance (not saved).
        """
        model = Submission(
            assignment_id=entity.assignment_id,
            student_id=entity.student_id,
            attempt_id=entity.attempt_id,
            status=entity.status.value,
            content=entity.content,
            attempt_number=entity.attempt_number,
            raw_score=entity.raw_score.value if entity.raw_score else None,
            final_score=entity.final_score.value if entity.final_score else None,
            late_penalty_applied=entity.late_penalty_applied,
            feedback=entity.feedback,
            graded_by_id=entity.graded_by,
            graded_at=entity.graded_at,
            submitted_at=entity.submitted_at
        )
        
        if entity.id:
            model.id = entity.id
        
        return model
    
    @staticmethod
    def update_model(model: Submission, entity: SubmissionEntity) -> Submission:
        """
        Update existing Django model from entity.
        
        Args:
            model: Existing Submission model to update.
            entity: SubmissionEntity with updated data.
        
        Returns:
            Updated Submission model (not saved).
        """
        model.status = entity.status.value
        model.content = entity.content
        model.raw_score = entity.raw_score.value if entity.raw_score else None
        model.final_score = entity.final_score.value if entity.final_score else None
        model.late_penalty_applied = entity.late_penalty_applied
        model.feedback = entity.feedback
        model.graded_by_id = entity.graded_by
        model.graded_at = entity.graded_at
        model.submitted_at = entity.submitted_at
        
        return model