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
# Analytics
# ----------------------
def exercise_stats(exercise_id: str) -> Dict[str, Any]:
    qs = ExerciseAttemptModel.objects.filter(exercise_id=exercise_id)
    total = qs.count()
    avg_score = float(qs.aggregate(avg=Avg("score"))["avg"] or 0)
    passed = qs.filter(score__gte=50).count()
    return {"exercise_id": exercise_id, "total_attempts": total, "avg_score": avg_score, "passed": passed}


def export_results_csv(exercise_id: str) -> Tuple[str, bytes]:
    qs = ExerciseAttemptModel.objects.filter(exercise_id=exercise_id).select_related("student").prefetch_related("answers__question")
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["attempt_id", "student_id", "score", "question_id", "answer", "correct"])
    for att in qs:
        for ans in att.answers.all():
            writer.writerow([att.id, att.student_id, att.score, ans.question_id, ans.answer, ans.correct])
    return f"exercise_{exercise_id}_results.csv", buf.getvalue().encode("utf-8")