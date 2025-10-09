from dataclasses import dataclass, field
from datetime import datetime, timezone, UTC
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

from assignments.domain.value_objects.score import Score
from assignments.domain.value_objects.due_date import DueDate
from assignments.domain.value_objects.late_penalty import LatePenalty
from assignments.domain.value_objects.attempts_config import AttemptsConfig
from assignments.domain.value_objects.rubric_criterion import RubricCriterionScore
from assignments.domain.events.events import (
    AssignmentCreatedEvent, AssignmentPublishedEvent,
    SubmissionCreatedEvent, SubmissionSubmittedEvent,
    SubmissionGradedEvent, SubmissionReturnedEvent
)
from assignments.domain.entities.assignment import AssignmentEntity

logger = logging.getLogger(__name__)



class SubmissionStatus(str, Enum):
    """Status of a submission."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    LATE = "late"
    GRADING = "grading"
    GRADED = "graded"
    RETURNED = "returned"
    RESUBMITTED = "resubmitted"



@dataclass
class SubmissionEntity:
    """
    Student submission entity with grading logic.
    """
    # Identity
    id: Optional[str] = None
    
    # Relationships
    assignment_id: str = ""
    student_id: str = ""
    attempt_id: Optional[str] = None
    
    # Submission data
    status: SubmissionStatus = SubmissionStatus.DRAFT
    content: str = ""
    attempt_number: int = 1
    
    # Grading
    raw_score: Optional[Score] = None
    final_score: Optional[Score] = None
    late_penalty_applied: Decimal = Decimal('0.00')
    rubric_scores: List[RubricCriterionScore] = field(default_factory=list)
    
    # Feedback
    feedback: str = ""
    graded_by: Optional[str] = None
    graded_at: Optional[datetime] = None
    
    # Timestamps
    submitted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Domain events
    _events: List[Any] = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        """Initialize entity."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
    
    # --- Validation ---
    
    def validate(self) -> None:
        """Validate submission invariants."""
        if not self.assignment_id:
            raise ValueError("Submission must be linked to an assignment")
        
        if not self.student_id:
            raise ValueError("Submission must be linked to a student")
        
        if self.attempt_number < 1:
            raise ValueError("Attempt number must be at least 1")
        
        if self.raw_score and self.final_score:
            if self.raw_score.max_value != self.final_score.max_value:
                raise ValueError("Raw and final scores must have same max value")
    
    # --- Business Logic ---
    
    def submit(
        self,
        assignment: AssignmentEntity,
        submission_time: Optional[datetime] = None
    ) -> None:
        """
        Submit the assignment for grading.
        
        Args:
            assignment: The assignment being submitted for.
            submission_time: Time of submission (defaults to now).
        
        Raises:
            ValueError: If submission is not valid.
        """
        if self.status not in [SubmissionStatus.DRAFT, SubmissionStatus.RETURNED]:
            raise ValueError(f"Cannot submit from status {self.status}")
        
        if not assignment.is_available_for_submission(submission_time):
            raise ValueError("Assignment is not available for submission")
        
        self.validate()
        
        submission_time = submission_time or datetime.now(timezone.utc)
        self.submitted_at = submission_time
        
        # Determine if late
        is_late = (
            assignment.due_date and
            assignment.due_date.is_past_due(submission_time)
        )
        
        if is_late and not assignment.accepts_late_submissions():
            raise ValueError("Late submissions are not accepted for this assignment")
        
        self.status = SubmissionStatus.LATE if is_late else SubmissionStatus.SUBMITTED
        self.updated_at = submission_time
        
        self._add_event(SubmissionSubmittedEvent(
            submission_id=self.id,
            assignment_id=self.assignment_id,
            student_id=self.student_id,
            submitted_at=submission_time,
            is_late=is_late,
            attempt_number=self.attempt_number,
            occurred_at=datetime.now(UTC)
        ))
        
        logger.info(
            f"Submission {self.id} submitted by {self.student_id} "
            f"for assignment {self.assignment_id} (attempt {self.attempt_number})"
        )
    
    def start_grading(self, grader_id: str) -> None:
        """Mark submission as being graded."""
        if self.status not in [SubmissionStatus.SUBMITTED, SubmissionStatus.LATE]:
            raise ValueError(f"Cannot grade submission with status {self.status}")
        
        self.status = SubmissionStatus.GRADING
        self.graded_by = grader_id
        self.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Grading started for submission {self.id} by {grader_id}")
    
    def apply_grade(
        self,
        raw_score: Score,
        assignment: AssignmentEntity,
        grader_id: str,
        feedback: str = "",
        rubric_scores: Optional[List[RubricCriterionScore]] = None
    ) -> None:
        """
        Apply a grade to the submission.
        
        Args:
            raw_score: The raw score before penalties.
            assignment: The assignment entity.
            grader_id: ID of the person grading.
            feedback: Grading feedback.
            rubric_scores: Optional rubric criterion scores.
        """
        if self.status not in [SubmissionStatus.GRADING, SubmissionStatus.SUBMITTED, SubmissionStatus.LATE]:
            raise ValueError(f"Cannot grade submission with status {self.status}")
        
        if raw_score.max_value != assignment.max_score:
            raise ValueError("Score max value must match assignment max score")
        
        self.raw_score = raw_score
        self.feedback = feedback
        self.graded_by = grader_id
        self.graded_at = datetime.now(timezone.utc)
        
        # Calculate final score with penalties
        if self.submitted_at:
            final, penalty = assignment.calculate_final_score(raw_score, self.submitted_at)
            self.final_score = final
            self.late_penalty_applied = penalty
        else:
            self.final_score = raw_score
            self.late_penalty_applied = Decimal('0.00')
        
        if rubric_scores:
            self.rubric_scores = rubric_scores
        
        self.status = SubmissionStatus.GRADED
        self.updated_at = self.graded_at
        
        self._add_event(SubmissionGradedEvent(
            submission_id=self.id,
            assignment_id=self.assignment_id,
            student_id=self.student_id,
            raw_score=float(raw_score.value),
            final_score=float(self.final_score.value),
            graded_by=grader_id,
            graded_at=self.graded_at,
            occurred_at=datetime.now(UTC)
        ))
        
        logger.info(
            f"Submission {self.id} graded: {self.final_score} "
            f"(raw: {self.raw_score}, penalty: {self.late_penalty_applied}%)"
        )
    
    def return_to_student(self) -> None:
        """Return graded submission to student."""
        if self.status != SubmissionStatus.GRADED:
            raise ValueError("Can only return graded submissions")
        
        self.status = SubmissionStatus.RETURNED
        self.updated_at = datetime.now(timezone.utc)
        
        self._add_event(SubmissionReturnedEvent(
            submission_id=self.id,
            assignment_id=self.assignment_id,
            student_id=self.student_id,
            returned_at=self.updated_at,
            occurred_at=datetime.now(UTC)
        ))
        
        logger.info(f"Submission {self.id} returned to student {self.student_id}")
    
    def is_passing(self, assignment: AssignmentEntity) -> Optional[bool]:
        """
        Check if submission is passing.
        Returns None if not yet graded or no passing score defined.
        """
        if not self.final_score or not assignment.passing_score:
            return None
        
        return self.final_score.is_passing(assignment.passing_score)
    
    # --- Events ---
    
    def _add_event(self, event: Any) -> None:
        """Add a domain event."""
        self._events.append(event)
    
    def collect_events(self) -> List[Any]:
        """Collect and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events
    
    # --- Serialization ---
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'assignment_id': self.assignment_id,
            'student_id': self.student_id,
            'attempt_id': self.attempt_id,
            'status': self.status.value,
            'content': self.content,
            'attempt_number': self.attempt_number,
            'raw_score': self.raw_score.to_dict() if self.raw_score else None,
            'final_score': self.final_score.to_dict() if self.final_score else None,
            'late_penalty_applied': float(self.late_penalty_applied),
            'rubric_scores': [rs.to_dict() for rs in self.rubric_scores],
            'feedback': self.feedback,
            'graded_by': self.graded_by,
            'graded_at': self.graded_at.isoformat() if self.graded_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubmissionEntity':
        """Create from dictionary."""
        raw_score = None
        if data.get('raw_score'):
            rs = data['raw_score']
            raw_score = Score(
                value=Decimal(str(rs['value'])),
                max_value=Decimal(str(rs['max_value']))
            )
        
        final_score = None
        if data.get('final_score'):
            fs = data['final_score']
            final_score = Score(
                value=Decimal(str(fs['value'])),
                max_value=Decimal(str(fs['max_value']))
            )
        
        rubric_scores = []
        for rs_data in data.get('rubric_scores', []):
            rubric_scores.append(RubricCriterionScore(
                criterion_id=rs_data['criterion_id'],
                criterion_name=rs_data['criterion_name'],
                max_points=Decimal(str(rs_data['max_points'])),
                points_awarded=Decimal(str(rs_data['points_awarded'])),
                level_name=rs_data.get('level_name'),
                feedback=rs_data.get('feedback', '')
            ))
        
        return cls(
            id=data.get('id'),
            assignment_id=data['assignment_id'],
            student_id=data['student_id'],
            attempt_id=data.get('attempt_id'),
            status=SubmissionStatus(data.get('status', 'draft')),
            content=data.get('content', ''),
            attempt_number=data.get('attempt_number', 1),
            raw_score=raw_score,
            final_score=final_score,
            late_penalty_applied=Decimal(str(data.get('late_penalty_applied', '0.00'))),
            rubric_scores=rubric_scores,
            feedback=data.get('feedback', ''),
            graded_by=data.get('graded_by'),
            graded_at=datetime.fromisoformat(data['graded_at']) if data.get('graded_at') else None,
            submitted_at=datetime.fromisoformat(data['submitted_at']) if data.get('submitted_at') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )