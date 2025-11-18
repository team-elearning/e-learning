import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict

class TagDomain(BaseModel):
    """
    Domain Model đại diện cho một Tag.
    """
    id: uuid.UUID
    name: str
    slug: str

    # Cho phép Pydantic đọc dữ liệu từ object (Django Model)
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, model: Any) -> "TagDomain":
        """
        Factory method tạo TagDomain từ Django Tag model.
        """
        return cls(
            id=model.id,
            name=model.name,
            slug=model.slug
        )

    def to_dict(self) -> dict:
        """
        Chuyển đổi domain thành dictionary.
        """
        return self.model_dump()