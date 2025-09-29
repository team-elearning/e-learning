import re
import uuid
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from activities.domains.exercise_attempt_domain import ExerciseAttemptDomain
from activities.domains.exercise_answer_domain import ExerciseAnswerDomain
from activities.domains.question_domain import QuestionDomain
from activities.domains.exercise_domain import ExerciseDomain


# ---------- Helpers ----------
def now_utc() -> datetime:
    return datetime.utcnow()

def normalize_text(s: str) -> str:
    s = s or ""
    s = s.strip().lower()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'[^\w\s]', '', s)  # remove punctuation for basic normalization
    return s

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


class ExerciseAttemptDict(TypedDict):
    id: str
    exercise_id: str
    student_id: Optional[int]
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    score: Optional[float]
    metadata: Dict[str, Any]


class ExerciseAttemptDomain:
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_FINISHED = "finished"
    STATUS_ABANDONED = "abandoned"

    def __init__(self, id: str, exercise_id: str, student_id: Optional[int],
                 started_at: datetime, finished_at: Optional[datetime], status: str,
                 score: Optional[float], metadata: Dict[str,Any] = None, exercise: Optional[ExerciseDomain] = None):
        self.id = id
        self.exercise_id = exercise_id
        self.student_id = student_id
        self.started_at = started_at
        self.finished_at = finished_at
        self.status = status
        self.score = score
        self.metadata = metadata or {}
        # answers keyed by question_id
        self.answers: Dict[str, ExerciseAnswerDomain] = {}
        # optionally keep a reference to the parent ExerciseDomain to perform scoring
        self.exercise = exercise

    @classmethod
    def from_model(cls, model, exercise_domain: Optional[ExerciseDomain] = None) -> "ExerciseAttemptDomain":
        att = cls(
            id=str(model.id),
            exercise_id=str(getattr(model, 'exercise_id', getattr(model, 'exercise').id)),
            student_id=getattr(model, 'student_id', getattr(model, 'student', None).id if getattr(model, 'student', None) else None),
            started_at=model.started_at,
            finished_at=model.finished_at,
            status=getattr(model, 'status', 'in_progress'),
            score=model.score,
            metadata=getattr(model, 'metadata', {}) or {},
            exercise=exercise_domain
        )
        # load answers if present
        if hasattr(model, 'answers'):
            for a in model.answers.all():
                ad = ExerciseAnswerDomain(
                    id=str(a.id),
                    attempt_id=str(a.attempt.id),
                    question_id=str(a.question.id),
                    answer=a.answer,
                    correct=a.correct,
                    score=a.answer.get('score') if a.answer.get('score') else a.correct and 1.0 or 0.0
                )
                att.answers[ad.question_id] = ad
        return att

    def time_limit_seconds(self) -> Optional[int]:
        return self.metadata.get('time_limit_seconds')

    def time_elapsed_seconds(self) -> float:
        return (now_utc() - self.started_at).total_seconds()

    def time_remaining_seconds(self) -> Optional[float]:
        tl = self.time_limit_seconds()
        if not tl:
            return None
        remaining = tl - self.time_elapsed_seconds()
        return max(0.0, remaining)

    def add_or_update_answer(self, question: QuestionDomain, answer_payload: Dict[str,Any]) -> ExerciseAnswerDomain:
        if self.status != self.STATUS_IN_PROGRESS:
            raise ValueError("Cannot add answer to an attempt that is not in progress.")
        # scoring via question domain
        score_result = question.score_answer(answer_payload)
        ans = ExerciseAnswerDomain(
            id=str(uuid.uuid4()),
            attempt_id=self.id,
            question_id=question.id,
            answer=answer_payload,
            correct=bool(score_result.get('correct')),
            score=float(score_result.get('score', 0.0))
        )
        self.answers[question.id] = ans
        return ans

    def compute_score(self) -> float:
        # total points obtained / total possible points * 100 (percentage)
        if not self.exercise:
            raise ValueError("Attempt must be constructed with exercise domain reference to compute score.")
        total_possible = self.exercise.total_possible_points()
        if total_possible == 0:
            return 0.0
        obtained = sum((a.score or 0.0) for a in self.answers.values())
        pct = (obtained / total_possible) * 100.0
        # round to 2 decimals
        self.score = round(pct, 2)
        return self.score

    def finalize(self) -> Dict[str, Any]:
        # enforce time limit
        tl = self.time_limit_seconds()
        if tl is not None and self.time_elapsed_seconds() > tl:
            # optionally auto-submit remaining questions as blank or partial
            self.status = self.STATUS_FINISHED
            self.finished_at = now_utc()
            # compute score with whatever answers have been provided
            final_score = self.compute_score()
            return {"status": self.status, "score": final_score, "reason": "time_limit_exceeded"}
        # otherwise normal finalize
        self.status = self.STATUS_FINISHED
        self.finished_at = now_utc()
        final_score = self.compute_score()
        return {"status": self.status, "score": final_score, "reason": "submitted"}

    def summary(self) -> Dict[str, Any]:
        """Return summary suitable for UI: per-question breakdown + overall score."""
        per_q = []
        for q in (self.exercise.questions if self.exercise else []):
            ans = self.answers.get(q.id)
            per_q.append({
                "question_id": q.id,
                "prompt": q.prompt,
                "points": q.total_points(),
                "answer": ans.answer if ans else None,
                "score": ans.score if ans else 0.0,
                "correct": ans.correct if ans else False,
            })
        return {
            "attempt_id": self.id,
            "exercise_id": self.exercise_id,
            "student_id": self.student_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "score": self.score,
            "questions": per_q
        }