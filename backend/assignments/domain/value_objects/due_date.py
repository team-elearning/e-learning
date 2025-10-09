# assignments/domain/value_objects/due_date.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import re



@dataclass(frozen=True)
class DueDate:
    """
    Value object for due dates with timezone awareness.
    Handles late submission calculations.
    """
    due_at: datetime
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate date constraints."""
        # Ensure timezone awareness
        if self.due_at.tzinfo is None:
            raise ValueError("Due date must be timezone-aware")
        
        if self.available_from and self.available_from.tzinfo is None:
            raise ValueError("Available from date must be timezone-aware")
        
        if self.available_until and self.available_until.tzinfo is None:
            raise ValueError("Available until date must be timezone-aware")
        
        # Validate date ordering
        if self.available_from and self.available_from > self.due_at:
            raise ValueError("Available from date cannot be after due date")
        
        if self.available_until and self.available_until < self.due_at:
            raise ValueError("Available until date cannot be before due date")
    
    def is_available_now(self, current_time: Optional[datetime] = None) -> bool:
        """Check if assignment is currently available."""
        now = current_time or datetime.now(timezone.utc)
        
        if self.available_from and now < self.available_from:
            return False
        
        if self.available_until and now > self.available_until:
            return False
        
        return True
    
    def is_past_due(self, submission_time: Optional[datetime] = None) -> bool:
        """Check if a submission is past the due date."""
        check_time = submission_time or datetime.now(timezone.utc)
        return check_time > self.due_at
    
    def days_late(self, submission_time: datetime) -> int:
        """Calculate number of days late (rounded up)."""
        if not self.is_past_due(submission_time):
            return 0
        
        delta = submission_time - self.due_at
        # Round up to nearest day
        return max(1, (delta.days + 1) if delta.seconds > 0 else delta.days)
    
    def hours_late(self, submission_time: datetime) -> int:
        """Calculate number of hours late (rounded up)."""
        if not self.is_past_due(submission_time):
            return 0
        
        delta = submission_time - self.due_at
        hours = delta.total_seconds() / 3600
        return max(1, int(hours) + (1 if hours % 1 > 0 else 0))
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'due_at': self.due_at.isoformat(),
            'available_from': self.available_from.isoformat() if self.available_from else None,
            'available_until': self.available_until.isoformat() if self.available_until else None
        }
