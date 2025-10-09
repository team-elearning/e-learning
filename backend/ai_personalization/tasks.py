# ai_personalization/tasks.py

from celery import shared_task
from .models import LearningEvent
from .services import update_mastery

@shared_task
def process_event(event_id):
    try:
        ev = LearningEvent.objects.get(id=event_id)
    except LearningEvent.DoesNotExist:
        return
    # For submit events: update mastery
    if ev.event_type == 'submit':
        correct = ev.detail.get('correct', False)
        lesson = ev.lesson
        if lesson is None:
            return
        from .models import ContentSkill
        skills = ContentSkill.objects.filter(lesson=lesson)
        for s in skills:
            update_mastery(ev.user, s.skill, correct, alpha=0.2)
    # For complete, you may also schedule spaced repetition entries (not implemented here)
