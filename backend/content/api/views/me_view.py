from rest_framework import generics, permissions
from content import models
from content.serializers import CourseSerializer, ExplorationSerializer

class MyCoursesListView(generics.ListAPIView):
    """
    GET /api/me/courses/
    Lấy danh sách các khóa học do tôi sở hữu (để quản lý).
    """
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return models.Course.objects.filter(owner=user)

class MyExplorationsListView(generics.ListAPIView):
    """
    GET /api/me/explorations/
    Lấy danh sách các exploration do tôi sở hữu.
    """
    serializer_class = ExplorationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return models.Exploration.objects.filter(owner=user)
