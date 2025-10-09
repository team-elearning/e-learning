# assignments/domain/services/assignment_service.py
from typing import Dict, Optional, List, Any
from datetime import datetime

from assignments.domain.factories.assignment_factory import AssignmentFactory
from assignments.domain.value_objects.score import Score
from assignments.domain.entities.assignment import Assignment
from backend.assignments.domain.events.events import AssignmentSubmittedEvent, GradeAssignedEvent



class AssignmentService:
    def __init__(self):
        self.store: Dict[str, Assignment] = {}

    def create_assignment(self, title: str, teacher_id: str, **kwargs):
        a = AssignmentFactory.create(title=title, teacher_id=teacher_id, **kwargs)
        self.store[a.id] = a
        return a

    def get_assignment(self, assignment_id: str) -> Assignment:
        a = self.store.get(assignment_id)
        if a is None:
            raise KeyError("Assignment not found.")
        return a
    
    def submit(self, assignment_id: str, student_id: str, content: Dict[str, Any], attachments: Optional[List[str]] = None, now: Optional[datetime] = None) -> AssignmentSubmittedEvent:
        a = self.get_assignment(assignment_id)
        return a.submit(student_id=student_id, content=content, now=now)

    def auto_grade(self, assignment_id: str, submission_id: str) -> Score:
        a = self.get_assignment(assignment_id)
        return a.auto_grade_submission(submission_id)

    def grade(self, assignment_id: str, submission_id: str, score: Score, grader_id: Optional[str] = None, feedback: Optional[str] = None) -> GradeAssignedEvent:
        a = self.get_assignment(assignment_id)
        return a.grade_submission(submission_id=submission_id, score=score, grader_id=grader_id, feedback=feedback)
