from datetime import datetime
from dataclasses import dataclass
from uuid import UUID
from typing import Optional, Dict, Any


# --- Domain cho Reset Progress ---
@dataclass
class ResetProgressResultDomain:
    enrollment_id: UUID
    status: str      # 'success'
    reset_at: datetime
    message: str