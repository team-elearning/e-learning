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
from activities.services import (
    get_exercise,
    list_exercises,
    save_exercise,
    delete_exercise,
    add_question,
    delete_question,
    add_choice,
    delete_choice,
    start_attempt,
    submit_answer,
    finalize_attempt,
    regrade_attempt,
    get_attempt_summary,
    exercise_stats,
    export_results_csv,
)
from activities.services import ServiceError, NotFoundError, ValidationError, PermissionDenied
from activities.api.permissions import IsAdminOrReadOnly

# Models used for permission checks or lookups (optional)
from django.apps import apps
ExerciseModel = apps.get_model("activities", "Exercise")
ExerciseAttemptModel = apps.get_model("activities", "ExerciseAttempt")
ExerciseAnswerModel = apps.get_model("activities", "ExerciseAnswer")


class ExerciseListCreateView(APIView):
    """
    GET /api/activities/exercises/  -> list exercises (optional filtering by lesson)
    POST /api/activities/exercises/ -> create exercise (admin/instructor)
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request: Request):
        lesson_id = request.query_params.get("lesson_id")
        filters = {}
        if lesson_id:
            filters["lesson_id"] = lesson_id
        domains = list_exercises(filters=filters)
        data = [ExerciseModelSerializer.from_domain(d) for d in domains]
        return Response(data)

    def post(self, request: Request):
        serializer = ExerciseModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # map to domain
        domain = serializer.to_domain()
        try:
            created = save_exercise(domain)
        except (ValidationError, ServiceError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ExerciseModelSerializer.from_domain(created), status=status.HTTP_201_CREATED)


class ExerciseDetailView(APIView):
    """
    GET /api/activities/exercises/{id}/
    PATCH /api/activities/exercises/{id}/
    DELETE /api/activities/exercises/{id}/
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request: Request, exercise_id: str):
        try:
            domain = get_exercise(exercise_id)
        except NotFoundError:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(ExerciseModelSerializer.from_domain(domain))

    def patch(self, request: Request, exercise_id: str):
        # partial update; load model, then merge changes using serializer
        try:
            model = ExerciseModel.objects.prefetch_related("questions__choices").get(id=exercise_id)
        except ExerciseModel.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ExerciseModelSerializer(instance=model, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        domain = serializer.to_domain()
        try:
            updated = save_exercise(domain)
        except (ValidationError, ServiceError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ExerciseModelSerializer.from_domain(updated))

    def delete(self, request: Request, exercise_id: str):
        try:
            delete_exercise(exercise_id)
        except NotFoundError:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)