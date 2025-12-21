from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional


class ActivityLogItemInput(BaseModel):
    """
    DTO đại diện cho 1 hành động đơn lẻ trong Batch.
    """
    action: str = Field(..., min_length=1, description="Mã hành động (VD: VIDEO_HEARTBEAT)")
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict, description="Metadata bổ sung (timestamp, scroll_depth...)")
    session_id: Optional[str] = None
    is_critical: bool = False


class ActivityBatchInput(BaseModel):
    """
    DTO đại diện cho cả gói tin Batch gửi lên từ Client.
    """
    model_config = ConfigDict(from_attributes=True)

    batch: List[ActivityLogItemInput] = Field(..., min_length=1, description="Danh sách các hành động")