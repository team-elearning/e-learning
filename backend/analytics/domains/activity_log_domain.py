import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class ActivityLogDomain:
    """
    Domain Entity đại diện cho một hành động của User.
    Decoupled hoàn toàn khỏi Django Model.
    """
    id: int
    user_id: uuid.UUID
    username: str
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    payload: Dict[str, Any]
    timestamp: datetime
    session_id: Optional[str]

    @classmethod
    def from_model(cls, model_instance):
        """Factory method để convert từ Django Model sang Domain"""
        return cls(
            id=model_instance.id,
            user_id=model_instance.user_id,
            username=model_instance.user.username, # Giả định user được select_related
            action=model_instance.action,
            entity_type=model_instance.entity_type,
            entity_id=model_instance.entity_id,
            payload=model_instance.payload,
            timestamp=model_instance.timestamp,
            session_id=model_instance.session_id
        )