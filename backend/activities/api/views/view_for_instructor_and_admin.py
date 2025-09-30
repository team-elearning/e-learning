from typing import Any, Dict
from django.http import HttpResponse
from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.parsers import JSONParser

# Import your serializers and services
from activities.serializers import (
    ExerciseModelSerializer,
    QuestionModelSerializer,
    ChoiceModelSerializer,
    StartAttemptSerializer,
    SubmitAnswerSerializer,
    FinalizeAttemptSerializer,
    ExerciseAttemptModelSerializer,
    ExerciseAnswerModelSerializer,
    exercise_domain_to_response,
    attempt_domain_to_response,
)
from activities.services import attempt_service, exercise_service, analytic_service
from activities.services import ServiceError, NotFoundError, ValidationError, PermissionDenied
from activities.api.permissions import IsAdminOrReadOnly



class RegradeAttemptView(APIView):
    """
    POST /api/activities/attempts/{attempt_id}/regrade/
    Admin/instructor only.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request: Request, attempt_id: str):
        try:
            result = attempt_service.regrade_attempt(attempt_id)
        except NotFoundError:
            return Response({"detail": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_200_OK)


class ManualGradeView(APIView):
    """
    POST /api/activities/attempts/{attempt_id}/grade/
    Body: {"question_id": "...", "score": 2.0, "comment": "notes"}
    Admin/instructor only.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request: Request, attempt_id: str):
        data = request.data
        qid = data.get("question_id")
        score = data.get("score")
        comment = data.get("comment")
        if qid is None or score is None:
            return Response({"detail": "question_id and score are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # call service function (we expect it to exist in services.activities)
            answer_domain = attempt_service.manual_grade_answer(attempt_id, qid, request.user, float(score), comment)
        except NotFoundError:
            return Response({"detail": "Attempt or answer not found"}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ExerciseAnswerModelSerializer.from_domain(answer_domain), status=status.HTTP_200_OK)


class ExerciseStatsView(APIView):
    """
    GET /api/activities/exercises/{exercise_id}/stats/
    Admin/instructor only (you can loosen permission if teachers should view).
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get(self, request: Request, exercise_id: str):
        try:
            stats = exercise_service.exercise_stats(exercise_id)
        except NotFoundError:
            return Response({"detail": "Exercise not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(stats)


class ExportResultsView(APIView):
    """
    GET /api/activities/exercises/{exercise_id}/export/
    Returns CSV file attachment. Admin/instructor only.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get(self, request: Request, exercise_id: str):
        try:
            filename, content = analytic_service.export_results_csv(exercise_id)
        except NotFoundError:
            return Response({"detail": "Exercise not found"}, status=status.HTTP_404_NOT_FOUND)
        resp = HttpResponse(content, content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp