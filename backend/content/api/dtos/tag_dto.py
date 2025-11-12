from pydantic import BaseModel, ConfigDict
import uuid

class TagOutput(BaseModel):
    """DTO cho Tag (để lồng vào Course output)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID # Giả định Tag dùng UUID
    name: str # Giả định Tag có trường 'name'

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)