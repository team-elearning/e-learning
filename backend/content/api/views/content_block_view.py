from typing import Any, Dict
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from content import models
from content.serializers import (
    ContentBlockSerializer,
    AddContentBlockInputSerializer,
    ReorderItemsInputSerializer,
)

from custom_account.api.permissions import IsOwnerOrAdmin
from content.services.content_block_service import ContentBlockService

content_block_service = ContentBlockService()


class ContentBlockListCreateView(generics.ListCreateAPIView):
    """
    GET /api/lesson-versions/{lesson_version_id}/blocks/
    POST /api/lesson-versions/{lesson_version_id}/blocks/
    """
    serializer_class = ContentBlockSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        lv_id = self.kwargs.get("lesson_version_id")
        return models.ContentBlock.objects.filter(lesson_version_id=lv_id).order_by("position")

    def create(self, request, lesson_version_id=None, *args, **kwargs):
        serializer = AddContentBlockInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cmd = serializer.to_domain(lesson_version_id=lesson_version_id)
        created_domain = content_block_service.create_block(cmd)
        
        instance = models.ContentBlock.objects.get(id=created_domain.id)
        return Response(ContentBlockSerializer(instance).data, status=status.HTTP_201_CREATED)


class ContentBlockDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/content-blocks/{id}/
    PATCH /api/content-blocks/{id}/
    DELETE /api/content-blocks/{id}/
    """
    queryset = models.ContentBlock.objects.all()
    serializer_class = ContentBlockSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updates = serializer.validated_data
        updated_domain = content_block_service.update_block(block_id=instance.id, update_data=updates)
        if not updated_domain:
            return Response({"detail": "Cannot update content block"}, status=status.HTTP_400_BAD_REQUEST)
        
        instance.refresh_from_db()
        return Response(self.get_serializer(instance).data)


class ContentBlockReorderView(APIView):
    """
    POST /api/lesson-versions/{lesson_version_id}/blocks/reorder/
    body: [{"id": "<block_id>", "position": <pos>}, ...]
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request, lesson_version_id: str):
        serializer = ReorderItemsInputSerializer(data={"items": request.data})
        serializer.is_valid(raise_exception=True)
        
        try:
            # Check permissions on the course
            version = get_object_or_404(models.LessonVersion, id=lesson_version_id)
            self.check_object_permissions(request, version.lesson.module.course)

            reorder_command = serializer.to_domain(reorder_type='blocks')
            content_block_service.reorder_blocks(lesson_version_id=lesson_version_id, reorder_data=reorder_command)
            return Response({"status": "ok"})
        except Exception as ex:
            return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)
