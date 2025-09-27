from typing import List, Optional
from django.db import transaction

from content.models import Lesson, Module
from content.domains.lesson_domain import (
    LessonDomain, CreateLessonDomain, UpdateLessonDomain, PublishLessonDomain, ReorderLessonsDomain
)


class LessonService:
    """Service for managing lessons inside modules."""

    @transaction.atomic
    def create_lesson(self, input_data: CreateLessonDomain) -> LessonDomain:
        input_data.validate()
        module = Module.objects.get(id=input_data.module_id)
        lesson = Lesson.objects.create(
            module=module,
            title=input_data.title,
            position=input_data.position,
            content_type=input_data.content_type
        )
        return LessonDomain.from_model(lesson)

    def list_lessons(self, module_id: str) -> List[LessonDomain]:
        return [LessonDomain.from_model(l) for l in Lesson.objects.filter(module_id=module_id)]

    @transaction.atomic
    def update_lesson(self, lesson_id: str, update_data: UpdateLessonDomain) -> Optional[LessonDomain]:
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return None
        update_data.validate()
        if update_data.title: lesson.title = update_data.title
        if update_data.position is not None: lesson.position = update_data.position
        if update_data.content_type: lesson.content_type = update_data.content_type
        lesson.save()
        return LessonDomain.from_model(lesson)

    @transaction.atomic
    def publish_lesson(self, lesson_id: str, publish_data: PublishLessonDomain) -> Optional[LessonDomain]:
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return None
        publish_data.validate()
        lesson.published = publish_data.published
        lesson.save()
        return LessonDomain.from_model(lesson)

    @transaction.atomic
    def reorder_lessons(self, module_id: str, reorder_data: ReorderLessonsDomain) -> None:
        reorder_data.validate()
        for lesson_id, pos in reorder_data.order_map.items():
            Lesson.objects.filter(id=lesson_id, module_id=module_id).update(position=pos)
