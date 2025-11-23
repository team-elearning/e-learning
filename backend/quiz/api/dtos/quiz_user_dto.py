from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator, computed_field
from datetime import datetime, timedelta
from typing import Optional, Any

from quiz.api.dtos.exam_dto import ExamPublicOutput

# ==========================================
# HELPER MIXIN (Để tái sử dụng to_dict)
# ==========================================
class BaseDTO(BaseModel):
    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Standard conversion to dictionary
        """
        return self.model_dump(exclude_none=exclude_none)

# ==========================================
# 1. Access Decision DTO (Quyết định vào thi)
# ==========================================
class AccessDecisionOutput(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    is_allowed: bool
    action: str  # 'start', 'resume', 'none'
    reason_message: str
    button_label: str
    ongoing_attempt_id: Optional[UUID] = None

# ==========================================
# 2. Quiz Preflight Output (Màn hình chờ)
# ==========================================
class QuizPreflightOutput(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    exam: ExamPublicOutput
    
    # Nested DTO
    access_decision: AccessDecisionOutput
    attempts_used: int