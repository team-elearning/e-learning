# ai_personalization/views.py

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import LearningEventSerializer, RecommendationLogSerializer
from .models import LearningEvent, RecommendationLog
from .tasks import process_event
from .services import RuleEngine

class LearningEventView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LearningEventSerializer

    def perform_create(self, serializer):
        ev = serializer.save(user=self.request.user)
        # enqueue background task
        process_event.delay(str(ev.id))

class NextRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        course_id = request.query_params.get('course_id')
        top_n = int(request.query_params.get('top_n', 3))
        if not course_id:
            return Response({'error': 'course_id required'}, status=status.HTTP_400_BAD_REQUEST)
        from content.models import Course
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'invalid course_id'}, status=status.HTTP_400_BAD_REQUEST)

        engine = RuleEngine(request.user, course)
        recs = engine.recommend(top_n=top_n)
        return Response({'recommendations': recs})

class RecommendationFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Body example:
        {
          "recommendation_id": "...",
          "action": "accepted"|"skipped"|"completed",
          "feedback": {"outcome": true, "attempts": 2}
        }
        """
        rec_id = request.data.get('recommendation_id')
        action = request.data.get('action')
        feedback = request.data.get('feedback', {})
        try:
            rec = RecommendationLog.objects.get(id=rec_id, user=request.user)
        except RecommendationLog.DoesNotExist:
            return Response({'error': 'invalid recommendation_id'}, status=status.HTTP_400_BAD_REQUEST)
        rec.acted_at = rec.acted_at or rec.shown_at
        rec.accepted = (action == 'accepted')
        rec.feedback = feedback
        rec.save()
        return Response({'status': 'ok'})

