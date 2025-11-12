from rest_framework import generics, permissions
from content import models
from content.serializers import CourseSerializer, LessonSerializer, ExplorationSerializer
from rest_framework.response import Response

class SearchView(generics.GenericAPIView):
    """
    GET /api/search/?q=<term>&type=<course|lesson|exploration>&category=<id>
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')
        search_type = request.query_params.get('type')
        category_id = request.query_params.get('category')
        
        if not query:
            return Response({"courses": [], "lessons": [], "explorations": []})

        results = {}

        # Search Courses
        if not search_type or search_type == 'course':
            courses = models.Course.objects.filter(title__icontains=query, published=True)
            if category_id:
                courses = courses.filter(categories__id=category_id)
            results['courses'] = CourseSerializer(courses, many=True).data

        # Search Lessons
        if not search_type or search_type == 'lesson':
            lessons = models.Lesson.objects.filter(title__icontains=query, published=True)
            if category_id:
                lessons = lessons.filter(module__course__categories__id=category_id)
            results['lessons'] = LessonSerializer(lessons, many=True).data
            
        # Search Explorations
        if not search_type or search_type == 'exploration':
            explorations = models.Exploration.objects.filter(title__icontains=query, published=True)
            if category_id:
                explorations = explorations.filter(category__id=category_id)
            results['explorations'] = ExplorationSerializer(explorations, many=True).data

        return Response(results)