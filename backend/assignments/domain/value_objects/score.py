# assignments/domain/value_objects/score.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import re


@dataclass(frozen=True)
class Score:
    """
    Immutable value object representing a score/grade.
    Ensures scores are always valid and within bounds.
    """
    value: Decimal
    max_value: Decimal
    
    def __post_init__(self):
        """Validate score invariants."""
        if self.value < Decimal('0'):
            raise ValueError(f"Score cannot be negative: {self.value}")
        if self.max_value <= Decimal('0'):
            raise ValueError(f"Max score must be positive: {self.max_value}")
        if self.value > self.max_value:
            raise ValueError(
                f"Score {self.value} exceeds maximum {self.max_value}"
            )
    
    def as_percentage(self) -> Decimal:
        """Return score as a percentage."""
        if self.max_value == Decimal('0'):
            return Decimal('0')
        return (self.value / self.max_value * Decimal('100')).quantize(Decimal('0.01'))
    
    def is_passing(self, passing_score: Decimal) -> bool:
        """Check if this score meets the passing threshold."""
        return self.value >= passing_score
    
    def apply_penalty(self, penalty_percent: Decimal) -> 'Score':
        """Return a new Score with penalty applied."""
        if penalty_percent < Decimal('0') or penalty_percent > Decimal('100'):
            raise ValueError(f"Penalty must be 0-100%: {penalty_percent}")
        
        penalty_amount = (self.value * penalty_percent / Decimal('100')).quantize(Decimal('0.01'))
        new_value = max(Decimal('0'), self.value - penalty_amount)
        return Score(value=new_value, max_value=self.max_value)
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'value': float(self.value),
            'max_value': float(self.max_value),
            'percentage': float(self.as_percentage())
        }
    
    def __str__(self) -> str:
        return f"{self.value}/{self.max_value} ({self.as_percentage()}%)"