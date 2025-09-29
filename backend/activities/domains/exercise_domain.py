import re
import uuid
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from backend.activities.domains.exercise_attempt_domain import ExerciseAttemptDomain


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


class ExerciseDict(TypedDict):
    id: str
    lesson_id: str
    title: str
    type: str
    settings: Dict[str, Any]
    published: bool
    created_on: Optional[datetime]
    updated_on: Optional[datetime]


class ExerciseDomain:
    ALLOWED_TYPES = {"quiz", "assignment"}  # you can expand
    def __init__(self, id: str, lesson_id: str, title: str, type: str,
                 settings: Optional[Dict[str,Any]] = None,
                 questions: Optional[List[QuestionDomain]] = None,
                 published: bool = False,
                 created_on: Optional[datetime] = None,
                 updated_on: Optional[datetime] = None):
        self.id = id
        self.lesson_id = lesson_id
        self.title = title
        self.type = type
        self.settings = settings or {}
        self.questions = questions or []
        self.published = published
        self.created_on = created_on
        self.updated_on = updated_on

    @classmethod
    def from_model(cls, model) -> "ExerciseDomain":
        q_domains = [QuestionDomain.from_model(q) for q in getattr(model, 'questions').all()] if hasattr(model, 'questions') else []
        settings = {}
        if hasattr(model, 'settings') and model.settings:
            settings = model.settings.__dict__ if isinstance(model.settings, object) else model.settings
        return cls(
            id=str(model.id),
            lesson_id=str(getattr(model, 'lesson_id', getattr(model, 'lesson').id)),
            title=model.title,
            type=model.type,
            settings=settings,
            questions=q_domains,
            published=getattr(model, 'published', False),
            created_on=getattr(model, 'created_on', None),
            updated_on=getattr(model, 'updated_on', None)
        )

    def validate(self):
        if not self.title:
            raise ValueError("Exercise title is required.")
        if self.type not in self.ALLOWED_TYPES:
            # allow unknown types but warn — here enforce
            raise ValueError(f"Invalid exercise type: {self.type}")
        if not self.questions:
            raise ValueError("Exercise should contain at least one question.")
        for q in self.questions:
            q.validate()

    def total_possible_points(self) -> float:
        return sum(q.total_points() for q in self.questions)

    def can_attempt(self, student_attempt_count: int) -> bool:
        max_attempts = self.settings.get('max_attempts')
        if max_attempts is None:
            return True
        return student_attempt_count < int(max_attempts)

    def create_attempt(self, student_id: Optional[int] = None) -> "ExerciseAttemptDomain":
        started = now_utc()
        metadata = {}
        # store per-exercise time_limit for attempt
        if 'time_limit_seconds' in self.settings and self.settings['time_limit_seconds']:
            metadata['time_limit_seconds'] = int(self.settings['time_limit_seconds'])
        return ExerciseAttemptDomain(
            id=str(uuid.uuid4()),
            exercise_id=self.id,
            student_id=student_id,
            started_at=started,
            finished_at=None,
            status="in_progress",
            score=None,
            metadata=metadata,
            exercise=self
        )