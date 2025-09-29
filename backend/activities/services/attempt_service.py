from typing import Optional, List, Dict, Any, Tuple
from django.apps import apps
from django.db import transaction
from django.db.models import Avg, F
from django.utils import timezone
import csv
import io

# Domain imports
from activities.domains.choice_domain import (
    ChoiceDomain,
)
from activities.domains.exercise_answer_domain import ExerciseAnswerDomain
from activities.domains.exercise_attempt_domain import ExerciseAttemptDomain
from activities.domains.exercise_domain import ExerciseDomain
from activities.domains.question_domain import QuestionDomain
from activities.services.exceptions import NotFoundError, ValidationError, PermissionDenied
from activities.services.exercise_service import get_exercise



# Models
ExerciseModel = apps.get_model('activities', 'Exercise')
QuestionModel = apps.get_model('activities', 'Question')
ChoiceModel = apps.get_model('activities', 'Choice')
ExerciseAttemptModel = apps.get_model('activities', 'ExerciseAttempt')
ExerciseAnswerModel = apps.get_model('activities', 'ExerciseAnswer')

# Optional models
ExerciseSettingsModel = getattr(apps.get_model('activities', 'ExerciseSettings'), '__call__', None)
HintModel = getattr(apps.get_model('activities', 'Hint'), '__call__', None)
QuestionStatModel = getattr(apps.get_model('activities', 'QuestionStat'), '__call__', None)


# ----------------------
# Attempt lifecycle
# ----------------------
def start_attempt(exercise_id: str, student_user) -> ExerciseAttemptDomain:
    exercise = get_exercise(exercise_id)
    student_id = student_user.id
    num_attempts = ExerciseAttemptModel.objects.filter(
        exercise_id=exercise_id, student=student_user).count()
    if not exercise.can_attempt(num_attempts):
        raise ValidationError("Max attempts reached.")

    attempt_domain = exercise.create_attempt(student_id=student_id)
    attempt_model = ExerciseAttemptModel.objects.create(
        id=attempt_domain.id,
        exercise_id=exercise_id,
        student=student_user,
        metadata=attempt_domain.metadata or {},
        started_at=attempt_domain.started_at,
    )
    return ExerciseAttemptDomain.from_model(attempt_model, exercise)


def submit_answer(attempt_id: str, question_id: str, answer_payload: Dict[str, Any], actor_user) -> ExerciseAnswerDomain:
    try:
        att = ExerciseAttemptModel.objects.get(id=attempt_id)
    except ExerciseAttemptModel.DoesNotExist:
        raise NotFoundError("Attempt not found")

    exercise = ExerciseDomain.from_model(att.exercise)
    attempt = ExerciseAttemptDomain.from_model(att, exercise_domain=exercise)

    if actor_user.id != attempt.student_id and not actor_user.is_staff:
        raise PermissionDenied("Not allowed to submit answer for this attempt")

    # check status
    if attempt.status != attempt.STATUS_IN_PROGRESS:
        raise ValidationError("Attempt already finished")

    question = QuestionDomain.from_model(QuestionModel.objects.get(id=question_id))
    answer_domain = attempt.add_or_update_answer(question, answer_payload)

    ExerciseAnswerModel.objects.update_or_create(
        attempt=att, question_id=question_id,
        defaults={"answer": answer_domain.answer, "correct": answer_domain.correct}
    )

    attempt.compute_score()
    att.score = attempt.score
    att.metadata = attempt.metadata
    att.save()

    return answer_domain


def finalize_attempt(attempt_id: str, actor_user=None, force=False) -> Dict[str, Any]:
    try:
        att = ExerciseAttemptModel.objects.get(id=attempt_id)
    except ExerciseAttemptModel.DoesNotExist:
        raise NotFoundError("Attempt not found")

    exercise = ExerciseDomain.from_model(att.exercise)
    attempt = ExerciseAttemptDomain.from_model(att, exercise_domain=exercise)

    if force:
        if not (actor_user and actor_user.is_staff):
            raise PermissionDenied("Only staff may force finalize.")
        attempt.finalize()
    else:
        attempt.finalize()

    att.score = attempt.score
    att.finished_at = attempt.finished_at
    att.metadata = attempt.metadata
    att.save()

    return attempt.summary()


def regrade_attempt(attempt_id: str) -> Dict[str, Any]:
    try:
        att = ExerciseAttemptModel.objects.get(id=attempt_id)
    except ExerciseAttemptModel.DoesNotExist:
        raise NotFoundError("Attempt not found")

    exercise = ExerciseDomain.from_model(att.exercise)
    attempt = ExerciseAttemptDomain.from_model(att, exercise_domain=exercise)

    # rescore all answers
    total = 0.0
    for ans in att.answers.all():
        q = QuestionDomain.from_model(ans.question)
        result = q.score_answer(ans.answer or {})
        ans.answer.update(score=result.get("score", 0))
        ans.correct = result.get("correct", False)
        ans.save()
        total += ans.answer["score"]

    exercise_total = exercise.total_possible_points()
    attempt.score = round((total / exercise_total) * 100, 2) if exercise_total else total
    att.score = attempt.score
    att.save()

    return {"attempt_id": attempt_id, "new_score": attempt.score}


def get_attempt_summary(attempt_id: str) -> Dict[str, Any]:
    att = ExerciseAttemptModel.objects.get(id=attempt_id)
    exercise = ExerciseDomain.from_model(att.exercise)
    attempt = ExerciseAttemptDomain.from_model(att, exercise_domain=exercise)
    return attempt.summary()