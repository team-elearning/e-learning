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



class RubricScoreMapper:
    """Maps rubric scores between models and value objects."""
    
    @staticmethod
    def to_value_object(model: SubmissionRubricScoreModel) -> RubricCriterionScore:
        """Convert model to value object."""
        return RubricCriterionScore(
            criterion_id=str(model.criterion.id),
            criterion_name=model.criterion.name,
            max_points=model.criterion.max_points,
            points_awarded=model.points_awarded,
            level_name=model.selected_level.name if model.selected_level else None,
            feedback=model.feedback
        )
    
    @staticmethod
    def to_model(
        vo: RubricCriterionScore,
        submission_id: str
    ) -> SubmissionRubricScoreModel:
        """
        Convert value object to model.
        Note: Requires criterion to exist in database.
        """
        criterion = RubricCriterion.objects.get(id=vo.criterion_id)
        
        model = SubmissionRubricScoreModel(
            submission_id=submission_id,
            criterion=criterion,
            points_awarded=vo.points_awarded,
            feedback=vo.feedback
        )
        
        return model