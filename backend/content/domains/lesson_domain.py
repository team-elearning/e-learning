import uuid
from datetime import datetime
from typing import Optional

from content.services.exceptions import DomainValidationError, InvalidOperation



class LessonDomain:
    VALID_CONTENT_TYPES = ("lesson", "exploration", "exercise", "quiz", "video")

    def __init__(self,
                 module_id: str,
                 title: str,
                 position: int = 0,
                 content_type: str = "lesson",
                 published: bool = False,
                 id: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.module_id = module_id
        self.title = title
        self.position = int(position)
        self.content_type = content_type
        self.published = published  # convenience flag; canonical source is versions
        self.validate()

    def validate(self):
        if not self.module_id:
            raise DomainValidationError("Lesson.module_id required.")
        if not self.title or not self.title.strip():
            raise DomainValidationError("Lesson.title required.")
        if self.content_type not in self.VALID_CONTENT_TYPES:
            raise DomainValidationError("Invalid Lesson.content_type.")

    def has_published_version(self) -> bool:
        return any(v.status == "published" for v in self.versions)

    def publish_version(self, version: int):
        target = self.get_version(version)
        # Business rule: cannot publish empty version
        if not target.content or (isinstance(target.content, dict) and not target.content.get("content_blocks") and not target.content.get("structure")):
            raise InvalidOperation("Cannot publish an empty lesson version.")
        # Unpublish any other published versions (domain enforces invariant)
        for v in self.versions:
            if v.status == "published" and v.version != version:
                v.status = "review"
                v.published_at = None
        target.status = "published"
        target.published_at = datetime.now()
        # update lesson flag
        self.published = True
        return target

    def unpublish_all_versions(self):
        for v in self.versions:
            if v.status == "published":
                v.status = "review"
                v.published_at = None
        self.published = False

    def to_dict(self):
        return {
            "id": self.id,
            "module_id": self.module_id,
            "title": self.title,
            "position": self.position,
            "content_type": self.content_type,
            "published": self.published,
            "versions": [v.to_dict() for v in self.versions]
        }

    @classmethod
    def from_model(cls, model):
        l = cls(module_id=str(getattr(model,'module_id',None) or ""), title=model.title, position=model.position, content_type=model.content_type, published=model.published, id=str(model.id))
        return l