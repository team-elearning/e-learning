# assignments/domain/entities/assignment.py
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

logger = logging.getLogger(__name__)



class AssignmentStatus(str, Enum):
    """Status of an assignment."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AssignmentType(str, Enum):
    """Type of assignment."""
    HOMEWORK = "homework"
    QUIZ = "quiz"
    PROJECT = "project"
    WORKSHEET = "worksheet"
    ESSAY = "essay"


@dataclass
class AssignmentEntity:
    """
    Core assignment entity with business logic.
    Represents a homework/assessment assignment.
    """
    # Identity
    id: Optional[str] = None
    
    # Basic info
    title: str = ""
    description: str = ""
    instructions: str = ""
    assignment_type: AssignmentType = AssignmentType.HOMEWORK
    status: AssignmentStatus = AssignmentStatus.DRAFT
    
    # Relationships
    classroom_id: Optional[str] = None
    lesson_id: Optional[str] = None
    teacher_id: Optional[str] = None
    
    # Grading configuration
    max_score: Decimal = Decimal('100.00')
    passing_score: Optional[Decimal] = None
    
    # Timing
    due_date: Optional[DueDate] = None
    
    # Settings
    allow_late_submissions: bool = True
    late_penalty: LatePenalty = field(default_factory=lambda: LatePenalty(
        penalty_percent_per_day=Decimal('10.00')
    ))
    attempts_config: AttemptsConfig = field(default_factory=lambda: AttemptsConfig(
        max_attempts=1
    ))
    is_group_assignment: bool = False
    auto_grade: bool = False
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Domain events (not persisted)
    _events: List[Any] = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        """Validate entity after initialization."""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
    
    # --- Validation ---
    
    def validate(self) -> None:
        """
        Validate all business rules and invariants.
        
        Raises:
            ValueError: If any validation fails.
        """
        if not self.title or not self.title.strip():
            raise ValueError("Assignment title is required")
        
        if len(self.title) > 255:
            raise ValueError("Assignment title cannot exceed 255 characters")
        
        if self.max_score <= Decimal('0'):
            raise ValueError("Max score must be positive")
        
        if self.passing_score and self.passing_score > self.max_score:
            raise ValueError("Passing score cannot exceed max score")
        
        if self.passing_score and self.passing_score < Decimal('0'):
            raise ValueError("Passing score cannot be negative")
        
        if not self.teacher_id:
            raise ValueError("Assignment must have a teacher")
        
        # Validate due date if present
        if self.due_date:
            try:
                self.due_date.is_available_now()
            except ValueError as e:
                raise ValueError(f"Invalid due date configuration: {e}")
    
    
    # --- Business Logic Methods ---
    
    def publish(self) -> None:
        """
        Publish the assignment, making it available to students.
        
        Raises:
            ValueError: If assignment is not in valid state to publish.
        """
        if self.status != AssignmentStatus.DRAFT:
            raise ValueError(f"Cannot publish assignment with status {self.status}")
        
        self.validate()
        
        self.status = AssignmentStatus.PUBLISHED
        self.updated_at = datetime.now(timezone.utc)
        
        self._add_event(AssignmentPublishedEvent(
            assignment_id=self.id,
            title=self.title,
            due_date=self.due_date.due_at if self.due_date else None,
            published_at=self.updated_at,
            occurred_at=datetime.now(UTC)
        ))
        
        logger.info(f"Assignment {self.id} published: {self.title}")
    
    def archive(self) -> None:
        """Archive the assignment."""
        if self.status == AssignmentStatus.ARCHIVED:
            raise ValueError("Assignment is already archived")
        
        self.status = AssignmentStatus.ARCHIVED
        self.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Assignment {self.id} archived: {self.title}")
    
    def is_available_for_submission(
        self,
        current_time: Optional[datetime] = None
    ) -> bool:
        """Check if assignment is available for submission."""
        if self.status != AssignmentStatus.PUBLISHED:
            return False
        
        if not self.due_date:
            return True
        
        return self.due_date.is_available_now(current_time)
    
    def accepts_late_submissions(self) -> bool:
        """Check if assignment accepts late submissions."""
        return self.allow_late_submissions
    
    def calculate_final_score(
        self,
        raw_score: Score,
        submission_time: datetime
    ) -> tuple[Score, Decimal]:
        """
        Calculate final score with penalties applied.
        
        Returns:
            Tuple of (final_score, penalty_applied)
        """
        if not self.due_date or not self.due_date.is_past_due(submission_time):
            return raw_score, Decimal('0.00')
        
        penalty = self.late_penalty.calculate_penalty(self.due_date, submission_time)
        final_score = self.late_penalty.apply_to_score(
            raw_score, self.due_date, submission_time
        )
        
        return final_score, penalty
    
    def can_submit_attempt(self, current_attempt: int) -> bool:
        try:
            """Check if another attempt can be submitted."""
            config = AttemptsConfig(
                max_attempts=self.attempts_config.max_attempts,
                current_attempt=current_attempt
            )
            return True
        except ValueError:
            return False
    
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
        """Convert entity to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'instructions': self.instructions,
            'assignment_type': self.assignment_type.value,
            'status': self.status.value,
            'classroom_id': self.classroom_id,
            'lesson_id': self.lesson_id,
            'teacher_id': self.teacher_id,
            'max_score': float(self.max_score),
            'passing_score': float(self.passing_score) if self.passing_score else None,
            'due_date': self.due_date.to_dict() if self.due_date else None,
            'allow_late_submissions': self.allow_late_submissions,
            'late_penalty': self.late_penalty.to_dict(),
            'attempts_config': self.attempts_config.to_dict(),
            'is_group_assignment': self.is_group_assignment,
            'auto_grade': self.auto_grade,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AssignmentEntity':
        """Create entity from dictionary."""
        due_date = None
        if data.get('due_date'):
            dd = data['due_date']
            due_date = DueDate(
                due_at=datetime.fromisoformat(dd['due_at']),
                available_from=datetime.fromisoformat(dd['available_from']) if dd.get('available_from') else None,
                available_until=datetime.fromisoformat(dd['available_until']) if dd.get('available_until') else None
            )
        
        late_penalty_data = data.get('late_penalty', {})
        late_penalty = LatePenalty(
            penalty_percent_per_day=Decimal(str(late_penalty_data.get('penalty_percent_per_day', '10.00'))),
            max_penalty_percent=Decimal(str(late_penalty_data.get('max_penalty_percent', '100.00'))),
            grace_period_hours=late_penalty_data.get('grace_period_hours', 0)
        )
        
        attempts_data = data.get('attempts_config', {})
        attempts_config = AttemptsConfig(
            max_attempts=attempts_data.get('max_attempts', 1),
            current_attempt=attempts_data.get('current_attempt', 1)
        )
        
        return cls(
            id=data.get('id'),
            title=data['title'],
            description=data.get('description', ''),
            instructions=data.get('instructions', ''),
            assignment_type=AssignmentType(data.get('assignment_type', 'homework')),
            status=AssignmentStatus(data.get('status', 'draft')),
            classroom_id=data.get('classroom_id'),
            lesson_id=data.get('lesson_id'),
            teacher_id=data.get('teacher_id'),
            max_score=Decimal(str(data.get('max_score', '100.00'))),
            passing_score=Decimal(str(data['passing_score'])) if data.get('passing_score') else None,
            due_date=due_date,
            allow_late_submissions=data.get('allow_late_submissions', True),
            late_penalty=late_penalty,
            attempts_config=attempts_config,
            is_group_assignment=data.get('is_group_assignment', False),
            auto_grade=data.get('auto_grade', False),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )