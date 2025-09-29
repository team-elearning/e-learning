import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Iterable, Tuple
from collections import deque

from content.services.exceptions import DomainValidationError, NotFoundError, InvalidOperation
from content.domains.module_domain import ModuleDomain


class CourseDomain:
    """
    Aggregate root: Course gồm nhiều Module; Module có Lesson; Lesson có LessonVersion.
    Business rules (encoded here):
    - Course.slug format validated here (but uniqueness must be checked by app layer).
    - Publish rules (default policy): course can be published only when:
        * it has >=1 module
        * and there exists at least one published lesson version in the course
      (You can call `publish()` with stricter flag `require_all_lessons_published=True`).
    - Course.owner can be None (system content).
    """

    def __init__(self,
                 title: str,
                 subject_id: Optional[str] = None,
                 description: Optional[str] = None,
                 grade: Optional[str] = None,
                 owner_id: Optional[int] = None,
                 slug: Optional[str] = None,
                 id: Optional[str] = None,
                 published: bool = False,
                 published_at: Optional[datetime] = None):
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.subject_id = subject_id
        self.description = description
        self.grade = grade
        self.owner_id = owner_id
        self.slug = slug
        self.published = published
        self.published_at = published_at
        # contained aggregates (in-memory)
        self.modules: List["ModuleDomain"] = []
        self.validate()

    def validate(self):
        if not self.title or not self.title.strip():
            raise DomainValidationError("Course.title is required.")
        if self.slug and (" " in self.slug or len(self.slug) < 2):
            raise DomainValidationError("Course.slug must be at least 2 chars and have no spaces.")
        # grade length check
        if self.grade and len(str(self.grade)) > 16:
            raise DomainValidationError("Course.grade too long.")

    # ---- Module manipulation (aggregate boundary) ----
    def add_module(self, title: str, position: Optional[int] = None) -> "ModuleDomain":
        if not title or not title.strip():
            raise DomainValidationError("Module title required.")
        position = position if position is not None else len(self.modules)
        if position < 0 or position > len(self.modules):
            raise DomainValidationError("position out of range.")
        # shift positions of existing modules if needed
        for m in self.modules:
            if m.position >= position:
                m.position += 1
        module = ModuleDomain(course_id=self.id, title=title, position=position)
        self.modules.append(module)
        # normalize to keep consistent ordering
        self._normalize_modules_positions()
        return module

    def remove_module(self, module_id: str):
        found = None
        for m in self.modules:
            if m.id == module_id:
                found = m
                break
        if not found:
            raise NotFoundError("Module not found in course.")
        self.modules.remove(found)
        self._normalize_modules_positions()

    def move_module(self, module_id: str, new_position: int):
        if new_position < 0 or new_position >= len(self.modules):
            raise DomainValidationError("new_position out of range.")
        module = next((m for m in self.modules if m.id == module_id), None)
        if not module:
            raise NotFoundError("Module not found.")
        self.modules.remove(module)
        self.modules.insert(new_position, module)
        self._normalize_modules_positions()

    def _normalize_modules_positions(self):
        # keep positions sequential 0..n-1
        self.modules.sort(key=lambda m: m.position)
        for idx, m in enumerate(self.modules):
            m.position = idx

    def get_module(self, module_id: str) -> "ModuleDomain":
        m = next((m for m in self.modules if m.id == module_id), None)
        if not m:
            raise NotFoundError("Module not found.")
        return m

    def list_module_summaries(self) -> List[Dict[str, Any]]:
        return [m.to_dict(summary=True) for m in self.modules]

    # ---- Publishing rules ----
    def can_publish(self, require_all_lessons_published: bool = False) -> Tuple[bool, str]:
        # Rule 1: must have at least one module
        if not self.modules:
            return False, "Course must contain at least one module."
        # Rule 2: must have at least one lesson with published version
        any_published = False
        for m in self.modules:
            for l in m.lessons:
                if l.has_published_version():
                    any_published = True
                    break
            if any_published:
                break
        if not any_published:
            return False, "Course must contain at least one lesson with a published version."
        # Rule 3 (optional strict): every lesson must have a published version
        if require_all_lessons_published:
            for m in self.modules:
                for l in m.lessons:
                    if not l.has_published_version():
                        return False, f"Lesson '{l.title}' must have a published version."
        return True, "OK"

    def publish(self, require_all_lessons_published: bool = False):
        ok, reason = self.can_publish(require_all_lessons_published=require_all_lessons_published)
        if not ok:
            raise InvalidOperation(f"Cannot publish course: {reason}")
        self.published = True
        self.published_at = str(uuid.uuid4())

    def unpublish(self):
        # no complex rule: unpublish allowed anytime
        self.published = False
        self.published_at = None

    # ---- Serialization helpers ----
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "subject_id": self.subject_id,
            "description": self.description,
            "grade": self.grade,
            "owner_id": self.owner_id,
            "slug": self.slug,
            "published": self.published,
            "published_at": self.published_at,
            "modules": [m.to_dict() for m in self.modules]
        }

    @classmethod
    def from_model(cls, model):
        """
        Optional helper: nếu có Django model, mapping sang domain.
        model expected to have attributes and related loaders for modules->lessons->versions.
        """
        c = cls(title=model.title, subject_id=(str(model.subject.id) if getattr(model,'subject',None) else None),
                description=model.description, grade=model.grade, owner_id=(getattr(model,'owner',None).id if getattr(model,'owner',None) else None),
                slug=getattr(model,'slug',None), id=str(model.id), published=model.published, published_at=getattr(model,'published_at',None))
        # If model has prefetched modules/lessons/versions we can build nested domain objects
        if hasattr(model, "modules_prefetched") and model.modules_prefetched:
            for mod_m in model.modules_prefetched:
                mod_d = ModuleDomain.from_model(mod_m)
                c.modules.append(mod_d)
        return c