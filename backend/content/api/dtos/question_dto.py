from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid



class QuestionCreateInput(BaseModel):
    """DTO cho một câu hỏi (lồng trong Quiz)"""
    id: Optional[uuid.UUID] = None # Dùng cho patch
    type: str
    position: int
    prompt: Dict[str, Any] = {}
    answer_payload: Dict[str, Any] = {}
    hint: Optional[Dict[str, Any]] = None


class QuestionUpdateInput(BaseModel):
    """
    DTO cho một câu hỏi khi PATCH.
    Tất cả các trường là Optional.
    """
    id: Optional[uuid.UUID] = None # Key để service C/U/D
    type: Optional[str] = None
    position: Optional[int] = None
    prompt: Optional[Dict[str, Any]] = None
    answer_payload: Optional[Dict[str, Any]] = None
    hint: Optional[Dict[str, Any]] = None
