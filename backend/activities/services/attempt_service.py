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


def manual_grade_answer(
    attempt_id: str,
    question_id: str,
    grader_user,
    score: float,
    comment: Optional[str] = None
) -> ExerciseAnswerDomain:
    """
    Manual grading for a given answer.

    Behaviour:
    - Only staff can manual-grade (PermissionDenied otherwise).
    - Finds the ExerciseAnswerModel for (attempt, question).
    - Writes `manual_score` and optionally `grader_comment` into answer JSON,
      also sets answer['score'] = manual_score to override automated score.
    - Sets `correct` flag based on max_points (if provided) or score > 0 rule.
    - Recomputes attempt total by summing per-answer raw points:
        order of precedence for each answer: manual_score -> stored score -> recompute via QuestionDomain
    - Converts raw total to percentage using exercise.total_possible_points().
    - Persists updated answer(s) and attempt.score.
    - Returns ExerciseAnswerDomain for the answer that was manually graded.
    """
    # Permission
    if not getattr(grader_user, "is_staff", False):
        raise PermissionDenied("Only staff can manually grade answers.")

    # Load attempt + answer
    try:
        att_model = ExerciseAttemptModel.objects.select_related("exercise").prefetch_related("answers__question").get(id=attempt_id)
    except ExerciseAttemptModel.DoesNotExist:
        raise NotFoundError("Attempt not found")

    try:
        answer_model = ExerciseAnswerModel.objects.get(attempt=att_model, question_id=question_id)
    except ExerciseAnswerModel.DoesNotExist:
        raise NotFoundError("Answer not found for grading.")

    # Update answer JSON with manual score and comment, persist
    answer_data = answer_model.answer if isinstance(answer_model.answer, dict) else (answer_model.answer or {})
    answer_data = dict(answer_data)  # defensive copy
    answer_data['manual_score'] = float(score)
    # Optionally store max_points if not present (not overriding)
    # answer_data.setdefault('max_points', answer_data.get('max_points'))
    if comment:
        answer_data['grader_comment'] = comment
    # Make manual score the authoritative stored score
    answer_data['score'] = float(score)

    # Determine correct flag using max_points if available, else score > 0
    max_points = answer_data.get('max_points')
    if max_points is not None:
        try:
            correct_flag = float(score) >= float(max_points)
        except Exception:
            correct_flag = float(score) > 0
    else:
        correct_flag = float(score) > 0

    answer_model.answer = answer_data
    answer_model.correct = bool(correct_flag)
    answer_model.save()

    # Recompute attempt total (raw points) by iterating all answers for this attempt
    total_obtained = 0.0
    # For answers without score we will compute using QuestionDomain.score_answer(...)
    for ans in att_model.answers.all():
        payload = ans.answer or {}
        # payload may be non-dict depending on your model; ensure dict
        if not isinstance(payload, dict):
            payload = {}
        s = None
        if 'manual_score' in payload:
            try:
                s = float(payload['manual_score'])
            except Exception:
                s = 0.0
        elif 'score' in payload:
            try:
                s = float(payload['score'])
            except Exception:
                s = None

        if s is None:
            # compute using question domain (automated scoring)
            try:
                question_dom = QuestionDomain.from_model(ans.question)
                result = question_dom.score_answer(payload)
                s = float(result.get('score', 0.0))
                # persist computed score and correctness for audit
                payload['score'] = s
                ans.answer = payload
                ans.correct = bool(result.get('correct', False))
                ans.save()
            except Exception:
                # fallback
                s = 0.0

        total_obtained += s

    # Convert total raw points -> percentage based on exercise total points
    exercise_domain = ExerciseDomain.from_model(att_model.exercise)
    exercise_total_points = exercise_domain.total_possible_points()
    if exercise_total_points and exercise_total_points > 0:
        new_pct = round((total_obtained / exercise_total_points) * 100.0, 2)
    else:
        # If no per-question points defined, keep raw total
        new_pct = round(total_obtained, 2)

    # Persist attempt score
    att_model.score = new_pct
    att_model.save()

    # Return domain object for the manually graded answer
    return ExerciseAnswerDomain(
        id=str(answer_model.id),
        attempt_id=str(att_model.id),
        question_id=str(question_id),
        answer=answer_model.answer,
        correct=answer_model.correct,
        score=answer_model.answer.get('manual_score', None) if isinstance(answer_model.answer, dict) else None
    )

