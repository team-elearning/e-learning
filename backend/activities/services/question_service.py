from typing import List, Dict, Any, Tuple
from django.db import transaction
from django.db.models import Avg
from django.apps import apps
import csv, io

# Domain imports
from activities.domains import (
    ExerciseDomain,
    QuestionDomain,
    ChoiceDomain,
    ExerciseAttemptDomain,
    ExerciseAnswerDomain,
)

# Models
ExerciseModel = apps.get_model("activities", "Exercise")
QuestionModel = apps.get_model("activities", "Question")
ChoiceModel = apps.get_model("activities", "Choice")
ExerciseAttemptModel = apps.get_model("activities", "ExerciseAttempt")
ExerciseAnswerModel = apps.get_model("activities", "ExerciseAnswer")



# ----------------------
# Question services
# ----------------------
def add_question(exercise_id: str, q_domain: QuestionDomain) -> QuestionDomain:
    ex = ExerciseModel.objects.get(id=exercise_id)
    q = QuestionModel.objects.create(
        exercise=ex, prompt=q_domain.prompt, meta=q_domain.meta or {}
    )
    return QuestionDomain.from_model(q)


def delete_question(question_id: str) -> None:
    QuestionModel.objects.filter(id=question_id).delete()