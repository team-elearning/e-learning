import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TypedDict, Union

from content.services.exceptions import DomainValidationError


class SubjectDict(TypedDict):
    id: str
    title: str
    slug: str


class SubjectDomain:
    def __init__(self, title: str, slug: str, id: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.slug = slug
        self.validate()

    def validate(self):
        if not self.title or not self.title.strip():
            raise DomainValidationError("Subject title required.")
        if not self.slug or " " in self.slug:
            raise DomainValidationError("Subject slug required and cannot contain spaces.")

    def to_dict(self):
        return {"id": self.id, "title": self.title, "slug": self.slug}

    @classmethod
    def from_model(cls, model):
        # model expected to have .id, .title, .slug
        return cls(title=model.title, slug=model.slug, id=str(model.id))