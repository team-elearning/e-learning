import uuid
from typing import Optional, List

from core.exceptions import DomainValidationError, LessonNotFoundError
from content.domains.lesson_domain import LessonDomain



class ModuleDomain:
    def __init__(self, course_id: str, title: str, position: int = 0, id: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.course_id = course_id
        self.title = title
        self.position = int(position)
        self.lessons: List["LessonDomain"] = []
        self.validate()

    def validate(self):
        if not self.course_id:
            raise DomainValidationError("Module.course_id required.")
        if not self.title or not self.title.strip():
            raise DomainValidationError("Module.title required.")
        if self.position < 0:
            raise DomainValidationError("Module.position must be >= 0")

    # def add_lesson(self, title: str, content_type: str = "lesson", position: Optional[int] = None) -> "LessonDomain":
    #     if not title or not title.strip():
    #         raise DomainValidationError("Lesson title required.")
    #     position = position if position is not None else len(self.lessons)
    #     if position < 0 or position > len(self.lessons):
    #         raise DomainValidationError("position out of range.")
    #     for l in self.lessons:
    #         if l.position >= position:
    #             l.position += 1
    #     lesson = LessonDomain(module_id=self.course_id + ":" + self.id, title=title, position=position, content_type=content_type)
    #     # Note: lesson.module_id intentionally encodes course+module key for uniqueness in-memory;
    #     # in persistence layer you'll map properly to Module FK.
    #     self.lessons.append(lesson)
    #     self._normalize_lessons_positions()
    #     return lesson

    # def remove_lesson(self, lesson_id: str):
    #     l = next((x for x in self.lessons if x.id == lesson_id), None)
    #     if not l:
    #         raise LessonNotFoundError("Lesson not found in module.")
    #     self.lessons.remove(l)
    #     self._normalize_lessons_positions()

    # def _normalize_lessons_positions(self):
    #     self.lessons.sort(key=lambda x: x.position)
    #     for idx, l in enumerate(self.lessons):
    #         l.position = idx

    # def get_lesson(self, lesson_id: str) -> "LessonDomain":
    #     l = next((x for x in self.lessons if x.id == lesson_id), None)
    #     if not l:
    #         raise LessonNotFoundError("Lesson not found.")
    #     return l

    def to_dict(self):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "title": self.title,
            "position": self.position,
            "lessons": [l.to_dict() for l in self.lessons]
        }

    @classmethod
    def from_model(cls, model):
        """Tạo domain từ model Module, lồng Lesson"""
        module_domain = cls(
            id=str(model.id),
            course_id=(str(getattr(model,'course_id', None)) or ""),
            title=model.title,
            position=model.position
        )

        # Service phải prefetch '...__lessons__...'
        for lesson_model in model.lessons.all():
            module_domain.lessons.append(
                LessonDomain.from_model_summary(lesson_model)
            )
            
        return module_domain
    

    @classmethod
    def from_model_metadata(cls, model):
        """Tạo domain từ model Module, lồng Lesson"""
        module_domain = cls(
            id=str(model.id),
            course_id=(str(getattr(model,'course_id', None)) or ""),
            title=model.title,
            position=model.position
        )
                   
        return module_domain
    
