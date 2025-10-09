from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import re



@dataclass(frozen=True)
class RubricCriterionScore:
    """
    Value object representing a score for a single rubric criterion.
    """
    criterion_id: str
    criterion_name: str
    max_points: Decimal
    points_awarded: Decimal
    level_name: Optional[str] = None
    feedback: str = ""
    
    def __post_init__(self):
        """Validate criterion score."""
        if self.max_points <= Decimal('0'):
            raise ValueError("Max points must be positive")
        if self.points_awarded < Decimal('0'):
            raise ValueError("Points awarded cannot be negative")
        if self.points_awarded > self.max_points:
            raise ValueError(
                f"Points awarded {self.points_awarded} exceeds max {self.max_points}"
            )
    
    def as_percentage(self) -> Decimal:
        """Return score as percentage of max points."""
        if self.max_points == Decimal('0'):
            return Decimal('0')
        return (self.points_awarded / self.max_points * Decimal('100')).quantize(Decimal('0.01'))
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'criterion_id': self.criterion_id,
            'criterion_name': self.criterion_name,
            'max_points': float(self.max_points),
            'points_awarded': float(self.points_awarded),
            'percentage': float(self.as_percentage()),
            'level_name': self.level_name,
            'feedback': self.feedback
        }