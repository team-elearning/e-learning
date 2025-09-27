from typing import List, Optional
from django.db import transaction
from django.contrib.auth import get_user_model

from content.models import Course, Subject
from content.domains.course_domain import (
    CourseDomain, CreateCourseDomain, UpdateCourseDomain,
    CoursePublishDomain, CourseAssignOwnerDomain
)

User = get_user_model()


class CourseService:
    """Application service for managing courses."""

    @transaction.atomic
    def create_course(self, input_data: CreateCourseDomain) -> CourseDomain:
        input_data.validate()
        subject = None
        if input_data.subject_id:
            subject = Subject.objects.filter(id=input_data.subject_id).first()
        owner = None
        if input_data.owner_id:
            owner = User.objects.filter(id=input_data.owner_id).first()
        course = Course.objects.create(
            subject=subject,
            title=input_data.title,
            description=input_data.description,
            grade=input_data.grade,
            owner=owner,
            published=False
        )
        return CourseDomain.from_model(course)

    def get_course(self, course_id: str) -> Optional[CourseDomain]:
        try:
            return CourseDomain.from_model(Course.objects.get(id=course_id))
        except Course.DoesNotExist:
            return None

    def list_courses(self, subject_id: Optional[str] = None, published: Optional[bool] = None) -> List[CourseDomain]:
        qs = Course.objects.all()
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if published is not None:
            qs = qs.filter(published=published)
        return [CourseDomain.from_model(c) for c in qs]

    @transaction.atomic
    def update_course(self, course_id: str, update_data: UpdateCourseDomain) -> Optional[CourseDomain]:
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return None
        update_data.validate()
        if update_data.title: course.title = update_data.title
        if update_data.description: course.description = update_data.description
        if update_data.grade: course.grade = update_data.grade
        course.save()
        return CourseDomain.from_model(course)

    @transaction.atomic
    def publish_course(self, course_id: str, publish_data: CoursePublishDomain) -> Optional[CourseDomain]:
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return None
        publish_data.validate()
        course.published = publish_data.published
        course.save()
        return CourseDomain.from_model(course)

    @transaction.atomic
    def assign_owner(self, course_id: str, assign_data: CourseAssignOwnerDomain) -> Optional[CourseDomain]:
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return None
        owner = User.objects.filter(id=assign_data.owner_id).first()
        if not owner:
            raise ValueError("Owner does not exist.")
        course.owner = owner
        course.save()
        return CourseDomain.from_model(course)
