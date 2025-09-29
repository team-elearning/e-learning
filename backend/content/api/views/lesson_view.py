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



class LessonListCreateView(generics.ListCreateAPIView):
    """
    GET /api/modules/{module_id}/lessons/
    POST /api/modules/{module_id}/lessons/
    """
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        module_id = self.kwargs.get("module_id")
        return models.Lesson.objects.filter(module_id=module_id)

    def create(self, request, module_id=None, *args, **kwargs):
        serializer = CreateLessonInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cmd = serializer.to_domain(module_id=module_id)
        created_domain = lesson_service.create_lesson(cmd)
        return Response(LessonSerializer.from_domain(created_domain), status=status.HTTP_201_CREATED)


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/lessons/{id}/
    PATCH /api/lessons/{id}/   (owner/admin)
    DELETE /api/lessons/{id}/
    """
    queryset = models.Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updates = serializer.validated_data
        updated_domain = lesson_service.update_lesson(lesson_id=instance.id, update_data=updates)
        if not updated_domain:
            return Response({"detail": "Cannot update lesson"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LessonSerializer.from_domain(updated_domain))


class LessonPublishView(APIView):
    """
    POST /api/lessons/{id}/publish/
    body example: {"published": true}
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request, lesson_id: str):
        published_flag = request.data.get("published", True)
        try:
            # service handles toggling
            updated = lesson_service.publish_lesson(lesson_id=lesson_id, publish_data={"published": published_flag})
            if not updated:
                return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(LessonSerializer.from_domain(updated))
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)