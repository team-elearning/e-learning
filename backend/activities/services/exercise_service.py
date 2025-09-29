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
from activities.services.exceptions import NotFoundError



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
# Exercise CRUD
# ----------------------
def get_exercise(exercise_id: str) -> ExerciseDomain:
    try:
        m = ExerciseModel.objects.prefetch_related('questions__choices').get(id=exercise_id)
    except ExerciseModel.DoesNotExist:
        raise NotFoundError("Exercise not found")
    return ExerciseDomain.from_model(m)


def list_exercises(filters: Dict[str, Any] = None) -> List[ExerciseDomain]:
    qs = ExerciseModel.objects.all()
    if filters:
        if filters.get("lesson_id"):
            qs = qs.filter(lesson_id=filters["lesson_id"])
        if filters.get("published") is not None:
            qs = qs.filter(published=filters["published"])
    return [ExerciseDomain.from_model(m) for m in qs.prefetch_related("questions__choices")]


@transaction.atomic
def save_exercise(domain: ExerciseDomain) -> ExerciseDomain:
    """Create or update exercise with nested questions/choices."""
    ex, _ = ExerciseModel.objects.update_or_create(
        id=domain.id,
        defaults=dict(
            lesson_id=domain.lesson_id,
            title=domain.title,
            type=domain.type,
            settings=domain.settings or {},
        )
    )

    # Sync questions
    seen_qids = []
    for qd in domain.questions:
        q, _ = QuestionModel.objects.update_or_create(
            id=qd.id,
            defaults=dict(exercise=ex, prompt=qd.prompt, meta=qd.meta or {})
        )
        seen_qids.append(q.id)
        # Sync choices
        seen_cids = []
        for cd in qd.choices:
            c, _ = ChoiceModel.objects.update_or_create(
                id=cd.id,
                defaults=dict(
                    question=q,
                    text=cd.text,
                    is_correct=cd.is_correct,
                    position=cd.position,
                )
            )
            seen_cids.append(c.id)
        q.choices.exclude(id__in=seen_cids).delete()
    ex.questions.exclude(id__in=seen_qids).delete()

    return ExerciseDomain.from_model(ex)


def delete_exercise(exercise_id: str) -> bool:
    deleted, _ = ExerciseModel.objects.filter(id=exercise_id).delete()
    if not deleted:
        raise NotFoundError("Exercise not found")
    return True
