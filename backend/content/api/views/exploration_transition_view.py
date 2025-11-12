from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from content import models
from content.serializers import ExplorationTransitionSerializer, AddExplorationTransitionInputSerializer
from content.services.exploration_service import ExplorationTransitionService
from custom_account.api.permissions import IsOwnerOrAdmin


class ExplorationTransitionListCreateView(generics.ListCreateAPIView):
    """
    GET /api/explorations/{exploration_id}/transitions/
    POST /api/explorations/{exploration_id}/transitions/
    """
    serializer_class = ExplorationTransitionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        exploration_id = self.kwargs.get("exploration_id")
        return models.ExplorationTransition.objects.filter(exploration_id=exploration_id)

    def create(self, request, exploration_id=None, *args, **kwargs):
        serializer = AddExplorationTransitionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cmd = serializer.to_domain(exploration_id=exploration_id)
        created_domain = ExplorationTransitionService.create_transition(cmd)
        return Response(ExplorationTransitionSerializer.from_domain(created_domain), status=status.HTTP_201_CREATED)


class ExplorationTransitionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.ExplorationTransition.objects.all()
    serializer_class = ExplorationTransitionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updates = serializer.validated_data
        # service may implement update_transition
        updated_domain = Exploration_transition_service.update_transition(transition_id=instance.id, update_data=updates)
        if not updated_domain:
            return Response({"detail": "Cannot update transition"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ExplorationTransitionSerializer.from_domain(updated_domain))
