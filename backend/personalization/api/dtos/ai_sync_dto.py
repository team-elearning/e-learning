from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from uuid import UUID



class AISyncInput(BaseModel):
    """Input cho việc trigger sync, có thể mở rộng sau này (vd: force=True)"""
    force_update: bool = False


class AISyncResultOutput(BaseModel):
    """Output trả về sau khi sync thành công"""
    model_config = ConfigDict(from_attributes=True)

    status: str
    message: str
    processed_count: int