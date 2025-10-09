# assignments/tests/test_domain.py
"""
Comprehensive unit tests for the assignments domain layer.
Tests entities, value objects, and business rules.
"""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from assignments.domain.value_objects.score import Score
from assignments.domain.value_objects.due_date import DueDate
from assignments.domain.value_objects.late_penalty import LatePenalty
from assignments.domain.value_objects.attempts_config import AttemptsConfig
from assignments.domain.value_objects.rubric_criterion import RubricCriterionScore
from assignments.domain.entities.assignment import AssignmentEntity, AssignmentStatus
from assignments.domain.entities.submission import SubmissionEntity, SubmissionStatus


class TestScore:
    """Test Score value object."""
    
    def test_valid_score_creation(self):
        """Test creating a valid score."""
        score = Score(value=Decimal('85.5'), max_value=Decimal('100'))
        assert score.value == Decimal('85.5')
        assert score.max_value == Decimal('100')
    
    def test_score_as_percentage(self):
        """Test percentage calculation."""
        score = Score(value=Decimal('85'), max_value=Decimal('100'))
        assert score.as_percentage() == Decimal('85.00')
        
        score2 = Score(value=Decimal('43'), max_value=Decimal('50'))
        assert score2.as_percentage() == Decimal('86.00')
    
    def test_score_negative_value_raises_error(self):
        """Test that negative scores raise an error."""
        with pytest.raises(ValueError, match="Score cannot be negative"):
            Score(value=Decimal('-10'), max_value=Decimal('100'))
    
    def test_score_exceeds_max_raises_error(self):
        """Test that scores exceeding max raise an error."""
        with pytest.raises(ValueError, match="exceeds maximum"):
            Score(value=Decimal('150'), max_value=Decimal('100'))
    
    def test_score_is_passing(self):
        """Test checking if score is passing."""
        score = Score(value=Decimal('85'), max_value=Decimal('100'))
        assert score.is_passing(Decimal('70')) is True
        assert score.is_passing(Decimal('90')) is False
    
    def test_apply_penalty(self):
        """Test applying penalty to score."""
        score = Score(value=Decimal('100'), max_value=Decimal('100'))
        penalized = score.apply_penalty(Decimal('10'))
        
        assert penalized.value == Decimal('90.00')
        assert penalized.max_value == Decimal('100')
        
        # Original score is unchanged (immutable)
        assert score.value == Decimal('100')
    
    def test_apply_large_penalty(self):
        """Test that penalty doesn't result in negative score."""
        score = Score(value=Decimal('30'), max_value=Decimal('100'))
        penalized = score.apply_penalty(Decimal('50'))
        
        assert penalized.value == Decimal('15.00')
        assert penalized.value >= Decimal('0')


class TestDueDate:
    """Test DueDate value object."""
    
    def test_valid_due_date_creation(self):
        """Test creating a valid due date."""
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        due_date = DueDate(due_at=due_at)
        assert due_date.due_at == due_at
    
    def test_due_date_must_be_timezone_aware(self):
        """Test that naive datetimes are rejected."""
        naive_date = datetime(2025, 12, 31, 23, 59, 59)
        with pytest.raises(ValueError, match="timezone-aware"):
            DueDate(due_at=naive_date)
    
    def test_is_past_due(self):
        """Test checking if submission is past due."""
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        due_date = DueDate(due_at=due_at)
        
        # Before due date
        early_time = datetime(2025, 12, 30, 12, 0, 0, tzinfo=timezone.utc)
        assert due_date.is_past_due(early_time) is False
        
        # After due date
        late_time = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        assert due_date.is_past_due(late_time) is True
    
    def test_days_late_calculation(self):
        """Test calculating days late."""
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        due_date = DueDate(due_at=due_at)
        
        # 1 day late
        late_1_day = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert due_date.days_late(late_1_day) == 1
        
        # 3 days late
        late_3_days = datetime(2026, 1, 3, 12, 0, 0, tzinfo=timezone.utc)
        assert due_date.days_late(late_3_days) == 3
        
        # Not late
        on_time = datetime(2025, 12, 30, 12, 0, 0, tzinfo=timezone.utc)
        assert due_date.days_late(on_time) == 0
    
    def test_is_available_now(self):
        """Test checking if assignment is available."""
        now = datetime(2025, 12, 15, 12, 0, 0, tzinfo=timezone.utc)
        available_from = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        available_until = datetime(2026, 1, 5, 23, 59, 59, tzinfo=timezone.utc)
        
        due_date = DueDate(
            due_at=due_at,
            available_from=available_from,
            available_until=available_until
        )
        
        assert due_date.is_available_now(now) is True
        
        # Too early
        too_early = datetime(2025, 11, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert due_date.is_available_now(too_early) is False
        
        # Too late
        too_late = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
        assert due_date.is_available_now(too_late) is False


class TestLatePenalty:
    """Test LatePenalty value object."""
    
    def test_calculate_penalty_not_late(self):
        """Test no penalty when not late."""
        penalty = LatePenalty(penalty_percent_per_day=Decimal('10'))
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        due_date = DueDate(due_at=due_at)
        
        on_time = datetime(2025, 12, 30, 12, 0, 0, tzinfo=timezone.utc)
        assert penalty.calculate_penalty(due_date, on_time) == Decimal('0.00')
    
    def test_calculate_penalty_one_day_late(self):
        """Test penalty for 1 day late."""
        penalty = LatePenalty(penalty_percent_per_day=Decimal('10'))
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        due_date = DueDate(due_at=due_at)
        
        late_1_day = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert penalty.calculate_penalty(due_date, late_1_day) == Decimal('10.00')
    
    def test_calculate_penalty_multiple_days_late(self):
        """Test penalty for multiple days late."""
        penalty = LatePenalty(penalty_percent_per_day=Decimal('15'))
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        due_date = DueDate(due_at=due_at)
        
        late_3_days = datetime(2026, 1, 3, 12, 0, 0, tzinfo=timezone.utc)
        assert penalty.calculate_penalty(due_date, late_3_days) == Decimal('45.00')
    
    def test_calculate_penalty_capped_at_max(self):
        """Test that penalty is capped at maximum."""
        penalty = LatePenalty(
            penalty_percent_per_day=Decimal('30'),
            max_penalty_percent=Decimal('80')
        )
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        due_date = DueDate(due_at=due_at)
        
        late_5_days = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
        # Would be 150% but capped at 80%
        assert penalty.calculate_penalty(due_date, late_5_days) == Decimal('80.00')
    
    def test_grace_period(self):
        """Test grace period functionality."""
        penalty = LatePenalty(
            penalty_percent_per_day=Decimal('10'),
            grace_period_hours=24
        )
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        due_date = DueDate(due_at=due_at)
        
        # Within grace period (12 hours late)
        within_grace = datetime(2026, 1, 1, 11, 59, 59, tzinfo=timezone.utc)
        assert penalty.calculate_penalty(due_date, within_grace) == Decimal('0.00')
        
        # After grace period (30 hours late)
        after_grace = datetime(2026, 1, 2, 5, 59, 59, tzinfo=timezone.utc)
        assert penalty.calculate_penalty(due_date, after_grace) > Decimal('0.00')
    
    def test_apply_to_score(self):
        """Test applying penalty to a score."""
        penalty = LatePenalty(penalty_percent_per_day=Decimal('10'))
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        due_date = DueDate(due_at=due_at)
        
        score = Score(value=Decimal('90'), max_value=Decimal('100'))
        late_1_day = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        penalized_score = penalty.apply_to_score(score, due_date, late_1_day)
        
        assert penalized_score.value == Decimal('81.00')  # 90 - 10% = 81
        assert score.value == Decimal('90')  # Original unchanged


class TestAttemptsConfig:
    """Test AttemptsConfig value object."""
    
    def test_unlimited_attempts(self):
        """Test unlimited attempts configuration."""
        config = AttemptsConfig(max_attempts=0, current_attempt=1)
        assert config.is_limited() is False
        assert config.has_attempts_remaining() is True
        assert config.attempts_remaining() is None
    
    def test_limited_attempts(self):
        """Test limited attempts configuration."""
        config = AttemptsConfig(max_attempts=3, current_attempt=1)
        assert config.is_limited() is True
        assert config.has_attempts_remaining() is True
        assert config.attempts_remaining() == 2
    
    def test_no_attempts_remaining(self):
        """Test when no attempts remain."""
        config = AttemptsConfig(max_attempts=3, current_attempt=3)
        assert config.has_attempts_remaining() is False
        assert config.attempts_remaining() == 0
    
    def test_increment_attempt(self):
        """Test incrementing attempt number."""
        config = AttemptsConfig(max_attempts=3, current_attempt=1)
        new_config = config.increment()
        
        assert new_config.current_attempt == 2
        assert config.current_attempt == 1  # Original unchanged
    
    def test_invalid_attempts_raises_error(self):
        """Test that invalid attempts raise errors."""
        with pytest.raises(ValueError):
            AttemptsConfig(max_attempts=-1, current_attempt=1)
        
        with pytest.raises(ValueError):
            AttemptsConfig(max_attempts=3, current_attempt=0)
        
        with pytest.raises(ValueError):
            AttemptsConfig(max_attempts=2, current_attempt=5)


class TestRubricCriterionScore:
    """Test RubricCriterionScore value object."""
    
    def test_valid_criterion_score(self):
        """Test creating a valid criterion score."""
        score = RubricCriterionScore(
            criterion_id='123',
            criterion_name='Grammar',
            max_points=Decimal('20'),
            points_awarded=Decimal('18'),
            level_name='Excellent',
            feedback='Great work!'
        )
        assert score.points_awarded == Decimal('18')
        assert score.as_percentage() == Decimal('90.00')
    
    def test_criterion_score_exceeds_max_raises_error(self):
        """Test that exceeding max points raises error."""
        with pytest.raises(ValueError, match="exceeds max"):
            RubricCriterionScore(
                criterion_id='123',
                criterion_name='Grammar',
                max_points=Decimal('20'),
                points_awarded=Decimal('25')
            )


class TestAssignmentEntity:
    """Test AssignmentEntity business logic."""
    
    def test_create_valid_assignment(self):
        """Test creating a valid assignment entity."""
        entity = AssignmentEntity(
            title="Math Homework 1",
            description="Chapter 1 exercises",
            teacher_id="teacher123",
            max_score=Decimal('100'),
            status=AssignmentStatus.DRAFT
        )
        entity.validate()
        assert entity.title == "Math Homework 1"
    
    def test_assignment_requires_title(self):
        """Test that assignment requires a title."""
        entity = AssignmentEntity(
            title="",
            teacher_id="teacher123"
        )
        with pytest.raises(ValueError, match="title is required"):
            entity.validate()
    
    def test_assignment_requires_teacher(self):
        """Test that assignment requires a teacher."""
        entity = AssignmentEntity(
            title="Math Homework",
            teacher_id=None
        )
        with pytest.raises(ValueError, match="must have a teacher"):
            entity.validate()
    
    def test_publish_assignment(self):
        """Test publishing an assignment."""
        entity = AssignmentEntity(
            id="assign123",
            title="Math Homework 1",
            teacher_id="teacher123",
            status=AssignmentStatus.DRAFT
        )
        
        entity.publish()
        
        assert entity.status == AssignmentStatus.PUBLISHED
        assert entity.updated_at is not None
        
        # Check event was emitted
        events = entity.collect_events()
        assert len(events) == 1
        assert events[0].assignment_id == "assign123"
    
    def test_cannot_publish_already_published(self):
        """Test that published assignment cannot be re-published."""
        entity = AssignmentEntity(
            title="Math Homework 1",
            teacher_id="teacher123",
            status=AssignmentStatus.PUBLISHED
        )
        
        with pytest.raises(ValueError, match="Cannot publish"):
            entity.publish()
    
    def test_archive_assignment(self):
        """Test archiving an assignment."""
        entity = AssignmentEntity(
            title="Math Homework 1",
            teacher_id="teacher123",
            status=AssignmentStatus.PUBLISHED
        )
        
        entity.archive()
        assert entity.status == AssignmentStatus.ARCHIVED
    
    def test_is_available_for_submission(self):
        """Test checking if assignment is available."""
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        due_date = DueDate(
            due_at=due_at,
            available_from=datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        )
        
        entity = AssignmentEntity(
            title="Math Homework 1",
            teacher_id="teacher123",
            status=AssignmentStatus.PUBLISHED,
            due_date=due_date
        )
        
        current_time = datetime(2025, 12, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert entity.is_available_for_submission(current_time) is True
        
        # Draft assignment not available
        entity.status = AssignmentStatus.DRAFT
        assert entity.is_available_for_submission(current_time) is False
    
    def test_calculate_final_score_with_penalty(self):
        """Test calculating final score with late penalty."""
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        due_date = DueDate(due_at=due_at)
        late_penalty = LatePenalty(penalty_percent_per_day=Decimal('10'))
        
        entity = AssignmentEntity(
            title="Math Homework 1",
            teacher_id="teacher123",
            max_score=Decimal('100'),
            due_date=due_date,
            late_penalty=late_penalty
        )
        
        raw_score = Score(value=Decimal('90'), max_value=Decimal('100'))
        late_submission = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        final_score, penalty = entity.calculate_final_score(raw_score, late_submission)
        
        assert penalty == Decimal('10.00')
        assert final_score.value == Decimal('81.00')
    
    def test_can_submit_attempt(self):
        """Test checking if another attempt can be submitted."""
        attempts_config = AttemptsConfig(max_attempts=3, current_attempt=1)
        
        entity = AssignmentEntity(
            title="Math Homework 1",
            teacher_id="teacher123",
            attempts_config=attempts_config
        )
        
        assert entity.can_submit_attempt(1) is True
        assert entity.can_submit_attempt(2) is True
        assert entity.can_submit_attempt(3) is True
        assert entity.can_submit_attempt(4) is False


class TestSubmissionEntity:
    """Test SubmissionEntity business logic."""
    
    def test_create_valid_submission(self):
        """Test creating a valid submission entity."""
        entity = SubmissionEntity(
            assignment_id="assign123",
            student_id="student456",
            content="My answer to the homework",
            attempt_number=1
        )
        entity.validate()
        assert entity.assignment_id == "assign123"
    
    def test_submission_requires_assignment(self):
        """Test that submission requires an assignment."""
        entity = SubmissionEntity(
            assignment_id="",
            student_id="student456"
        )
        with pytest.raises(ValueError, match="linked to an assignment"):
            entity.validate()
    
    def test_submit_assignment(self):
        """Test submitting an assignment."""
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        assignment = AssignmentEntity(
            id="assign123",
            title="Math Homework 1",
            teacher_id="teacher123",
            status=AssignmentStatus.PUBLISHED,
            due_date=DueDate(due_at=due_at)
        )
        
        submission = SubmissionEntity(
            assignment_id="assign123",
            student_id="student456",
            content="My answers",
            status=SubmissionStatus.DRAFT
        )
        
        submission_time = datetime(2025, 12, 30, 12, 0, 0, tzinfo=timezone.utc)
        submission.submit(assignment, submission_time)
        
        assert submission.status == SubmissionStatus.SUBMITTED
        assert submission.submitted_at == submission_time
        
        # Check event
        events = submission.collect_events()
        assert len(events) == 1
        assert events[0].is_late is False
    
    def test_submit_late_assignment(self):
        """Test submitting a late assignment."""
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        assignment = AssignmentEntity(
            id="assign123",
            title="Math Homework 1",
            teacher_id="teacher123",
            status=AssignmentStatus.PUBLISHED,
            due_date=DueDate(due_at=due_at),
            allow_late_submissions=True
        )
        
        submission = SubmissionEntity(
            assignment_id="assign123",
            student_id="student456",
            content="My late answers",
            status=SubmissionStatus.DRAFT
        )
        
        late_time = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        submission.submit(assignment, late_time)
        
        assert submission.status == SubmissionStatus.LATE
        
        events = submission.collect_events()
        assert events[0].is_late is True
    
    def test_cannot_submit_if_late_not_allowed(self):
        """Test that late submissions are rejected if not allowed."""
        due_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        assignment = AssignmentEntity(
            title="Math Homework 1",
            teacher_id="teacher123",
            status=AssignmentStatus.PUBLISHED,
            due_date=DueDate(due_at=due_at),
            allow_late_submissions=False
        )
        
        submission = SubmissionEntity(
            assignment_id="assign123",
            student_id="student456",
            status=SubmissionStatus.DRAFT
        )
        
        late_time = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        
        with pytest.raises(ValueError, match="Late submissions are not accepted"):
            submission.submit(assignment, late_time)
    
    def test_apply_grade_to_submission(self):
        """Test grading a submission."""
        assignment = AssignmentEntity(
            id="assign123",
            title="Math Homework 1",
            teacher_id="teacher123",
            max_score=Decimal('100'),
            due_date=DueDate(
                due_at=datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
            )
        )
        
        submission = SubmissionEntity(
            id="sub123",
            assignment_id="assign123",
            student_id="student456",
            status=SubmissionStatus.SUBMITTED,
            submitted_at=datetime(2025, 12, 30, 12, 0, 0, tzinfo=timezone.utc)
        )
        
        raw_score = Score(value=Decimal('85'), max_value=Decimal('100'))
        
        submission.apply_grade(
            raw_score=raw_score,
            assignment=assignment,
            grader_id="teacher123",
            feedback="Good work!"
        )
        
        assert submission.status == SubmissionStatus.GRADED
        assert submission.raw_score.value == Decimal('85')
        assert submission.final_score.value == Decimal('85')
        assert submission.feedback == "Good work!"
        assert submission.graded_at is not None
        
        # Check event
        events = submission.collect_events()
        assert len(events) == 1
    
    def test_apply_grade_with_late_penalty(self):
        """Test grading with late penalty applied."""
        assignment = AssignmentEntity(
            id="assign123",
            title="Math Homework 1",
            teacher_id="teacher123",
            max_score=Decimal('100'),
            due_date=DueDate(
                due_at=datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
            ),
            late_penalty=LatePenalty(penalty_percent_per_day=Decimal('10'))
        )
        
        submission = SubmissionEntity(
            id="sub123",
            assignment_id="assign123",
            student_id="student456",
            status=SubmissionStatus.LATE,
            submitted_at=datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)  # 2 days late
        )
        
        raw_score = Score(value=Decimal('90'), max_value=Decimal('100'))
        
        submission.apply_grade(
            raw_score=raw_score,
            assignment=assignment,
            grader_id="teacher123"
        )
        
        assert submission.raw_score.value == Decimal('90')
        assert submission.final_score.value == Decimal('72.00')  # 90 - 20% = 72
        assert submission.late_penalty_applied == Decimal('20.00')
    
    def test_is_passing(self):
        """Test checking if submission is passing."""
        assignment = AssignmentEntity(
            title="Math Homework 1",
            teacher_id="teacher123",
            max_score=Decimal('100'),
            passing_score=Decimal('70')
        )
        
        submission = SubmissionEntity(
            assignment_id="assign123",
            student_id="student456",
            final_score=Score(value=Decimal('85'), max_value=Decimal('100'))
        )
        
        assert submission.is_passing(assignment) is True
        
        submission.final_score = Score(value=Decimal('65'), max_value=Decimal('100'))
        assert submission.is_passing(assignment) is False
    
    def test_return_to_student(self):
        """Test returning graded submission to student."""
        submission = SubmissionEntity(
            id="sub123",
            assignment_id="assign123",
            student_id="student456",
            status=SubmissionStatus.GRADED
        )
        
        submission.return_to_student()
        
        assert submission.status == SubmissionStatus.RETURNED
        
        events = submission.collect_events()
        assert len(events) == 1