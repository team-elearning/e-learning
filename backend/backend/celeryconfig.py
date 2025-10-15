# celeryconfig.py (project root)
"""
Celery configuration for async task processing.
"""
from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic task schedule
app.conf.beat_schedule = {
    'update-skill-decay-daily': {
        'task': 'ai_personalization.tasks.batch_update_skill_decay',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'train-mastery-model-weekly': {
        'task': 'ai_personalization.tasks.train_mastery_prediction_model',
        'schedule': crontab(day_of_week=1, hour=3, minute=0),  # Weekly Monday 3 AM
    },
}