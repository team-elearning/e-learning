from dataclasses import dataclass
from typing import Dict, Any
from content.models import Category

@dataclass
class CategoryDomain:
    id: str = None
    name: str = ""
    slug: str = ""

    def to_model(self) -> Category:
        return Category(
            id=self.id,
            name=self.name,
            slug=self.slug,
        )

    @classmethod
    def from_model(cls, model: Category) -> "CategoryDomain":
        return cls(
            id=str(model.id),
            name=model.name,
            slug=model.slug,
        )

    # def apply_updates(self, updates: Dict[str, Any]):
    #     """Apply validated updates to the domain object."""
    #     if "name" in updates:
    #         self.name = updates["name"]
    #     if "slug" in updates:
    #         self.slug = updates["slug"]

    # def can_be_deleted(self) -> bool:
    #     """Business rule placeholder — return False if category has dependencies."""
    #     return True
