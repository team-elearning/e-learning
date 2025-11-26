# from rest_framework import generics, permissions
# from content import models
# from content.serializers import TagSerializer


# class TagListCreateView(generics.ListCreateAPIView):
#     queryset = models.Tag.objects.all()
#     serializer_class = TagSerializer
#     permission_classes = [permissions.IsAdminUser]


# class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = models.Tag.objects.all()
#     serializer_class = TagSerializer
#     permission_classes = [permissions.IsAdminUser]
