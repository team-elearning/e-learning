from rest_framework import generics, permissions
from content import models
from content.serializers import TagSerializer
from custom_account.api.permissions import IsAdminOrReadOnly

class TagListCreateView(generics.ListCreateAPIView):
    queryset = models.Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]

class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
