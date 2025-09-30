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


# -----------------------
# Attempt endpoints
# -----------------------
class StartAttemptView(APIView):
    """
    POST /api/activities/exercises/{exercise_id}/start/
    Starts an attempt for the authenticated student.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, exercise_id: str):
        # we expect the current authenticated user is the student
        try:
            attempt_domain = start_attempt(exercise_id, request.user)
        except NotFoundError:
            return Response({"detail": "Exercise not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        # return attempt summary (domain -> response)
        return Response(ExerciseAttemptModelSerializer.from_domain(attempt_domain), status=status.HTTP_201_CREATED)


class SubmitAnswerView(APIView):
    """
    POST /api/activities/attempts/{attempt_id}/answers/
    Payload: { "question_id": "...", "answer": {...} }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, attempt_id: str):
        serializer = SubmitAnswerSerializer(data={"attempt_id": attempt_id, **request.data})
        serializer.is_valid(raise_exception=True)
        try:
            ans_domain = submit_answer(
                attempt_id=attempt_id,
                question_id=str(serializer.validated_data["question_id"]),
                answer_payload=serializer.validated_data["answer"],
                actor_user=request.user,
            )
        except NotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        return Response(ExerciseAnswerModelSerializer.from_domain(ans_domain), status=status.HTTP_200_OK)


class FinalizeAttemptView(APIView):
    """
    POST /api/activities/attempts/{attempt_id}/finalize/
    Optional payload: { "force": true } (instructor override)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, attempt_id: str):
        serializer = FinalizeAttemptSerializer(data={"attempt_id": attempt_id, **request.data})
        serializer.is_valid(raise_exception=True)
        force = serializer.validated_data.get("force", False)
        try:
            summary = finalize_attempt(attempt_id, actor_user=request.user, force=force)
        except NotFoundError:
            return Response({"detail": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(summary, status=status.HTTP_200_OK)


class AttemptSummaryView(APIView):
    """
    GET /api/activities/attempts/{attempt_id}/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, attempt_id: str):
        try:
            summary = get_attempt_summary(attempt_id)
        except NotFoundError:
            return Response({"detail": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(summary, status=status.HTTP_200_OK)