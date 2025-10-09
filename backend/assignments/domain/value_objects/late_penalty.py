from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import re

from assignments.domain.value_objects.due_date import DueDate
from assignments.domain.value_objects.score import Score



@dataclass(frozen=True)
class LatePenalty:
    """
    Value object for calculating late submission penalties.
    """
    penalty_percent_per_day: Decimal
    max_penalty_percent: Decimal = Decimal('100.00')
    grace_period_hours: int = 0
    
    def __post_init__(self):
        """Validate penalty constraints."""
        if self.penalty_percent_per_day < Decimal('0'):
            raise ValueError("Penalty percent cannot be negative")
        if self.penalty_percent_per_day > Decimal('100'):
            raise ValueError("Penalty percent cannot exceed 100")
        if self.max_penalty_percent < Decimal('0'):
            raise ValueError("Max penalty cannot be negative")
        if self.max_penalty_percent > Decimal('100'):
            raise ValueError("Max penalty cannot exceed 100")
        if self.grace_period_hours < 0:
            raise ValueError("Grace period cannot be negative")
    
    def calculate_penalty(
        self,
        due_date: DueDate,
        submission_time: datetime
    ) -> Decimal:
        """
        Calculate the penalty percentage for a late submission.
        Returns the penalty as a percentage (0-100).
        """
        if not due_date.is_past_due(submission_time):
            return Decimal('0.00')
        
        # Check grace period
        hours_late = due_date.hours_late(submission_time)
        if hours_late <= self.grace_period_hours:
            return Decimal('0.00')
        
        # Calculate penalty
        days_late = due_date.days_late(submission_time)
        penalty = self.penalty_percent_per_day * Decimal(days_late)
        
        # Cap at maximum penalty
        return min(penalty, self.max_penalty_percent).quantize(Decimal('0.01'))
    
    def apply_to_score(
        self,
        score: Score,
        due_date: DueDate,
        submission_time: datetime
    ) -> Score:
        """Apply late penalty to a score."""
        penalty = self.calculate_penalty(due_date, submission_time)
        return score.apply_penalty(penalty)
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'penalty_percent_per_day': float(self.penalty_percent_per_day),
            'max_penalty_percent': float(self.max_penalty_percent),
            'grace_period_hours': self.grace_period_hours
        }