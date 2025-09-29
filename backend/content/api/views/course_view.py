from typing import Any, Dict
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from content import models
from content.serializers import (
    SubjectSerializer, CourseSerializer, ModuleSerializer, LessonSerializer,
    LessonVersionSerializer, ContentBlockSerializer, ExplorationSerializer,
    ExplorationStateSerializer, ExplorationTransitionSerializer,
    CreateCourseInputSerializer, AddModuleInputSerializer, CreateLessonInputSerializer,
    CreateLessonVersionInputSerializer, PublishLessonVersionInputSerializer,
    AddContentBlockInputSerializer, CreateExplorationInputSerializer,
    AddExplorationStateInputSerializer, AddExplorationTransitionInputSerializer,
    CourseDetailReadSerializer, ModuleReadSerializer, LessonReadSerializer,
    LessonVersionReadSerializer
)

from content.services.subject_service import SubjectService
from content.services.course_service import CourseService
from content.services.module_service import ModuleService
from content.services.lesson_service import LessonService
from content.services.lesson_version_service import LessonVersionService
from content.services.content_block_service import ContentBlockService
from content.services.exploration_service import (
    ExplorationService, ExplorationStateService, ExplorationTransitionService
)



class CourseListCreateView(generics.ListCreateAPIView):
    """
    GET /api/courses/?subject_id=&published=      -> list (public)
    POST /api/courses/                             -> create (auth)
    """
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = models.Course.objects.all()
        subject_id = self.request.query_params.get("subject_id")
        published = self.request.query_params.get("published")
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if published is not None:
            qs = qs.filter(published=(published.lower() == "true"))
        return qs

    def create(self, request, *args, **kwargs):
        serializer = CreateCourseInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cmd = serializer.to_domain()
        created_domain = course_service.create_course(cmd)
        return Response(CourseDetailReadSerializer.from_domain(created_domain), status=status.HTTP_201_CREATED)


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/courses/{id}/
    PATCH /api/courses/{id}/   (owner or admin)
    DELETE /api/courses/{id}/  (owner or admin)
    """
    queryset = models.Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updates = serializer.validated_data
        # prefer passing an "update DTO" to service; if service accepts dict, pass dict
        updated_domain = course_service.update_course(course_id=instance.id, update_data=updates)
        if not updated_domain:
            return Response({"detail": "Not found or cannot update"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CourseDetailReadSerializer.from_domain(updated_domain))


class CoursePublishView(APIView):
    """
    POST /api/courses/{id}/publish/
    body: {"require_all_lessons_published": false}  OR {"published": true}
    - Orchestrates domain-level checks (CourseDomain.can_publish)
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request, course_id: str):
        # minimal validation
        require_all = request.data.get("require_all_lessons_published", False)
        # get current domain via service
        course_domain = course_service.get_course(course_id)
        if not course_domain:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            # domain has publish() with rule enforcement; we call service to persist
            course_service.publish_course(course_id=course_id, publish_data=type("D", (), {"published": True, "require_all_lessons_published": require_all}))
            # fetch updated
            updated = course_service.get_course(course_id)
            return Response(CourseDetailReadSerializer.from_domain(updated))
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# Extra: enroll / progress endpoints (basic)
class CourseEnrollView(APIView):
    """
    POST /api/courses/{id}/enroll/ -> enroll current user
    DELETE /api/courses/{id}/enroll/ -> unenroll
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id: str):
        # Using course_service.enroll_user (if implemented)
        try:
            course = course_service.get_course(course_id)
            if not course:
                return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
            course_service.enroll_user(course_id=course_id, user_id=request.user.id)
            return Response({"success": True}, status=status.HTTP_200_OK)
        except AttributeError:
            # service not implemented: graceful decline
            return Response({"detail": "Enroll feature not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception as ex:
            return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id: str):
        try:
            course_service.unenroll_user(course_id=course_id, user_id=request.user.id)
            return Response({"success": True}, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({"detail": "Unenroll feature not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception as ex:
            return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)