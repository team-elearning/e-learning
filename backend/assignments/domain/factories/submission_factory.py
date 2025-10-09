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



class SubmissionFactory:
    """
    Factory for creating SubmissionEntity objects.
    """
    
    @staticmethod
    def create(
        assignment_id: str,
        student_id: str,
        content: str = "",
        attempt_number: int = 1,
        attempt_id: Optional[str] = None
    ) -> SubmissionEntity:
        """
        Create a new submission entity.
        
        Args:
            assignment_id: ID of the assignment.
            student_id: ID of the student.
            content: Submission content.
            attempt_number: Attempt number for this submission.
            attempt_id: Optional linked exercise attempt ID.
        
        Returns:
            Validated SubmissionEntity.
        
        Raises:
            ValueError: If validation fails.
        """
        if not assignment_id:
            raise ValueError("Assignment ID is required")
        
        if not student_id:
            raise ValueError("Student ID is required")
        
        if attempt_number < 1:
            raise ValueError("Attempt number must be at least 1")
        
        entity = SubmissionEntity(
            assignment_id=assignment_id,
            student_id=student_id,
            content=content,
            attempt_number=attempt_number,
            attempt_id=attempt_id,
            status=SubmissionStatus.DRAFT,
            created_at=datetime.now(timezone.utc)
        )
        
        entity.validate()
        
        logger.info(
            f"SubmissionFactory created submission for assignment {assignment_id} "
            f"by student {student_id} (attempt {attempt_number})"
        )
        
        return entity
    
    @staticmethod
    def create_draft(
        assignment_id: str,
        student_id: str,
        content: str = ""
    ) -> SubmissionEntity:
        """
        Create a draft submission (not yet submitted).
        
        Args:
            assignment_id: Assignment ID.
            student_id: Student ID.
            content: Draft content.
        
        Returns:
            SubmissionEntity in draft status.
        """
        return SubmissionFactory.create(
            assignment_id=assignment_id,
            student_id=student_id,
            content=content,
            attempt_number=1
        )