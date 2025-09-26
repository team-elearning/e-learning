from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from school.serializers import (
    ClassroomSerializer,
    ClassroomCreateSerializer,
    ClassroomUpdateSerializer,
)
from school.services import classroom_service


class ClassroomListCreateView(APIView):
    """GET: list classrooms, POST: create new classroom"""

    def get(self, request):
        classrooms = classroom_service.list_classrooms()
        data = [ClassroomSerializer.from_domain(c) for c in classrooms]
        return Response(data)

    def post(self, request):
        serializer = ClassroomCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.to_domain()
        classroom = classroom_service.create_classroom(domain)
        return Response(
            ClassroomSerializer.from_domain(classroom),
            status=status.HTTP_201_CREATED
        )


class ClassroomDetailView(APIView):
    """GET: retrieve classroom, PUT: update classroom, DELETE: archive"""

    def get(self, request, pk: int):
        classroom = classroom_service.get_classroom(pk)
        return Response(ClassroomSerializer.from_domain(classroom))

    def put(self, request, pk: int):
        serializer = ClassroomUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.to_domain(pk)
        classroom = classroom_service.update_classroom(domain)
        return Response(ClassroomSerializer.from_domain(classroom))

    def delete(self, request, pk: int):
        classroom_service.archive_classroom(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
