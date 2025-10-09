from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import re



@dataclass(frozen=True)
class AttemptsConfig:
    """
    Value object for managing attempt limits and policies.
    """
    max_attempts: int
    current_attempt: int = 1
    
    def __post_init__(self):
        """Validate attempt configuration."""
        if self.max_attempts < 0:
            raise ValueError("Max attempts cannot be negative (use 0 for unlimited)")
        if self.current_attempt < 1:
            raise ValueError("Current attempt must be at least 1")
        if self.is_limited() and self.current_attempt > self.max_attempts:
            raise ValueError(
                f"Current attempt {self.current_attempt} exceeds max {self.max_attempts}"
            )
    
    def is_limited(self) -> bool:
        """Check if attempts are limited."""
        return self.max_attempts > 0
    
    def has_attempts_remaining(self) -> bool:
        """Check if more attempts are available."""
        if not self.is_limited():
            return True
        return self.current_attempt < self.max_attempts
    
    def attempts_remaining(self) -> Optional[int]:
        """Get number of attempts remaining (None if unlimited)."""
        if not self.is_limited():
            return None
        return max(0, self.max_attempts - self.current_attempt)
    
    def increment(self) -> 'AttemptsConfig':
        """Return new config with incremented attempt number."""
        return AttemptsConfig(
            max_attempts=self.max_attempts,
            current_attempt=self.current_attempt + 1
        )
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            'max_attempts': self.max_attempts if self.is_limited() else None,
            'current_attempt': self.current_attempt,
            'attempts_remaining': self.attempts_remaining(),
            'has_remaining': self.has_attempts_remaining()
        }