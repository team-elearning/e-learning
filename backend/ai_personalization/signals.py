# ai_personalization/signals.py
"""
Django signals for automatic mastery updates and event processing.
Implements event-driven architecture for real-time personalization.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import LearningEvent, UserSkillMastery, ContentSkill
from .tasks import update_mastery_async, regenerate_recommendations
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=LearningEvent)
def process_learning_event(sender, instance, created, **kwargs):
    """
    Process learning events to update skill mastery.
    Triggered after each event save for real-time updates.
    """
    if not created:
        return
    
    # Only process events that indicate learning progress
    if instance.event_type not in ['submit', 'complete']:
        return
    
    if not instance.lesson:
        logger.warning(f"Event {instance.id} has no associated lesson")
        return
    
    try:
        # Get skills associated with this lesson
        skills = ContentSkill.objects.skills_for_lesson(instance.lesson)
        
        if not skills:
            logger.info(f"No skills mapped for lesson {instance.lesson.id}")
            return
        
        # Extract performance data from event
        correct = instance.detail.get('correct', False)
        time_spent = instance.detail.get('time_spent', 0)
        attempts = instance.detail.get('attempts', 1)
        
        # Queue async task for heavy computation
        update_mastery_async.delay(
            user_id=str(instance.user.id),
            skills=skills,
            correct=correct,
            time_spent=time_spent,
            attempts=attempts
        )
        
        # Invalidate user's recommendation cache
        cache_key = f"recommendations:{instance.user.id}"
        cache.delete(cache_key)
        
        logger.info(
            f"Queued mastery update for user {instance.user.id}, "
            f"skills: {skills}, correct: {correct}"
        )
        
    except Exception as e:
        logger.error(f"Error processing learning event {instance.id}: {str(e)}")


@receiver(post_save, sender=UserSkillMastery)
def on_mastery_update(sender, instance, created, **kwargs):
    """
    Trigger recommendation regeneration when mastery changes significantly.
    """
    if created:
        return
    
    # Check if mastery changed by more than threshold
    if hasattr(instance, '_old_mastery'):
        delta = abs(instance.mastery - instance._old_mastery)
        if delta > 0.2:  # 20% change threshold
            regenerate_recommendations.delay(
                user_id=str(instance.user.id),
                trigger_skill=instance.skill
            )
            logger.info(f"Queued recommendation regen for {instance.user.id}")


# Store old mastery value for comparison
from django.db.models.signals import pre_save

@receiver(pre_save, sender=UserSkillMastery)
def store_old_mastery(sender, instance, **kwargs):
    """Store old mastery value before update."""
    if instance.pk:
        try:
            old_instance = UserSkillMastery.objects.get(pk=instance.pk)
            instance._old_mastery = old_instance.mastery
        except UserSkillMastery.DoesNotExist:
            instance._old_mastery = 0.0