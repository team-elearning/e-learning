from typing import Any, Dict
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from content import models
from content.serializers import (
    ExplorationSerializer,
    CreateExplorationInputSerializer,
    FullExplorationSerializer,
)

from custom_account.api.permissions import IsOwnerOrAdmin
from content.services.exploration_service import (
    ExplorationService
)

exploration_service = ExplorationService()


class ExplorationListCreateView(generics.ListCreateAPIView):
    """
    GET /api/explorations/
    POST /api/explorations/
    """
    serializer_class = ExplorationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = models.Exploration.objects.filter(published=True)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return models.Exploration.objects.all()
        
        # For anonymous or regular users, only show published explorations
        return models.Exploration.objects.filter(published=True)

    def create(self, request, *args, **kwargs):
        serializer = CreateExplorationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if 'owner_id' not in serializer.validated_data and request.user.is_authenticated:
            serializer.validated_data['owner_id'] = request.user.id
        cmd = serializer.to_domain()
        created_domain = exploration_service.create_exploration(cmd)
        instance = models.Exploration.objects.get(id=created_domain.id)
        return Response(ExplorationSerializer(instance).data, status=status.HTTP_201_CREATED)


class ExplorationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/explorations/{id}/ (Returns full exploration structure)
    PUT /api/explorations/{id}/  (Saves the entire exploration from a giant JSON)
    PATCH /api/explorations/{id}/ (Saves simple metadata)
    DELETE /api/explorations/{id}/
    """
    queryset = models.Exploration.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    lookup_field = 'id'

    def get_serializer_class(self):
        # Use the full serializer for GET to return the entire structure for editing
        if self.request.method == 'GET':
            return FullExplorationSerializer
        # Use the basic serializer for PATCH (metadata updates)
        return ExplorationSerializer

    def update(self, request, *args, **kwargs):
        # PUT is for the giant JSON update from the editor
        if request.method == 'PUT':
            instance = self.get_object()
            try:
                updated_domain = exploration_service.update_exploration_from_json(instance.id, request.data)
                if not updated_domain:
                    return Response({"detail": "Update failed"}, status=status.HTTP_400_BAD_REQUEST)
                
                updated_instance = exploration_service.get_exploration_details(instance.id)
                read_serializer = FullExplorationSerializer(updated_instance)
                return Response(read_serializer.data)
            except Exception as ex:
                return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)
        
        # PATCH is for simple metadata updates
        return super().update(request, *args, **kwargs)


class ExplorationPlayerView(generics.RetrieveAPIView):
    """
    GET /api/explorations/{id}/player/
    Returns the full exploration data structure for the player.
    """
    queryset = models.Exploration.objects.filter(published=True)
    serializer_class = FullExplorationSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'


class ExplorationPublishView(APIView):
    """
    POST /api/explorations/{id}/publish/
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request, exploration_id: str):
        publish_flag = request.data.get("published", True)
        try:
            # The service should ideally run validation (e.g., graph is valid) before publishing
            updated = exploration_service.publish_exploration(exploration_id=exploration_id, publish_data={"published": publish_flag})
            if not updated:
                return Response({"detail": "Not found or validation failed"}, status=status.HTTP_400_BAD_REQUEST)
            return Response(ExplorationSerializer(updated).data)
        except Exception as ex:
            return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

class ExplorationUnpublishView(APIView):
    """
    POST /api/explorations/{id}/unpublish/
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request, exploration_id: str):
        try:
            updated = exploration_service.unpublish_exploration(exploration_id=exploration_id)
            if not updated:
                return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(ExplorationSerializer(updated).data)
        except Exception as ex:
            return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

class ExplorationMediaUploadView(APIView):
    """
    POST /api/explorations/{id}/media/upload/
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, exploration_id: str):
        # This is a placeholder. A full implementation would handle file storage (e.g., to S3)
        # and create a StateMedia object.
        file_obj = request.data.get('file')
        if not file_obj:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Dummy response
        file_url = f"/media/explorations/{exploration_id}/{file_obj.name}"
        return Response({"filepath": file_url}, status=status.HTTP_201_CREATED)