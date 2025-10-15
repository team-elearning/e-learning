# # ai_personalization/tasks.py

# from celery import shared_task
# from .models import LearningEvent
# from .services import update_mastery

# @shared_task
# def process_event(event_id):
#     try:
#         ev = LearningEvent.objects.get(id=event_id)
#     except LearningEvent.DoesNotExist:
#         return
#     # For submit events: update mastery
#     if ev.event_type == 'submit':
#         correct = ev.detail.get('correct', False)
#         lesson = ev.lesson
#         if lesson is None:
#             return
#         from .models import ContentSkill
#         skills = ContentSkill.objects.filter(lesson=lesson)
#         for s in skills:
#             update_mastery(ev.user, s.skill, correct, alpha=0.2)
#     # For complete, you may also schedule spaced repetition entries (not implemented here)


# ai_personalization/tasks.py
"""
Celery tasks for async processing of heavy AI computations.
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from typing import List
import logging
import numpy as np

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def update_mastery_async(self, user_id: str, skills: List[str], correct: bool, time_spent: float, attempts: int):
    """
    Async task to update skill mastery after learning event.
    
    Args:
        user_id: User UUID as string
        skills: List of skill identifiers
        correct: Whether the attempt was correct
        time_spent: Time spent in seconds
        attempts: Number of attempts
    """
    try:
        from .models import UserSkillMastery
        from .ai_engines import MasteryCalculator
        
        user = User.objects.get(id=user_id)
        
        for skill in skills:
            MasteryCalculator.update_mastery_from_event(
                user=user,
                skill=skill,
                correct=correct,
                time_spent=time_spent,
                attempts=attempts
            )
        
        logger.info(f"Updated mastery for user {user_id}, skills: {skills}")
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Mastery update failed: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True)
def regenerate_recommendations(self, user_id: str, trigger_skill: str = None):
    """
    Async task to regenerate recommendations after significant mastery change.
    
    Args:
        user_id: User UUID as string
        trigger_skill: Skill that triggered regeneration (optional)
    """
    try:
        from .ai_engines import RecommendationEngine
        from django.core.cache import cache
        
        user = User.objects.get(id=user_id)
        
        # Clear cache
        cache_key = f"recommendations:{user_id}"
        cache.delete(cache_key)
        
        # Generate new recommendations
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(
            student=user,
            limit=10,
            algorithm='hybrid'
        )
        
        logger.info(
            f"Regenerated {len(recommendations)} recommendations for user {user_id}"
            f"{f' (triggered by {trigger_skill})' if trigger_skill else ''}"
        )
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Recommendation regeneration failed: {str(e)}")


@shared_task
def train_mastery_prediction_model():
    """
    Periodic task to retrain the ML mastery prediction model.
    Should be run daily or weekly depending on data volume.
    """
    try:
        from .models import UserSkillMastery, LearningEvent
        from .utils import extract_features_from_events
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        import pickle
        import os
        
        logger.info("Starting mastery prediction model training...")
        
        # Collect training data
        masteries = UserSkillMastery.objects.filter(
            practice_count__gte=5  # Only include skills with sufficient data
        ).select_related('user')
        
        training_data = []
        for mastery in masteries:
            # Get events for this user-skill pair
            events = LearningEvent.objects.filter(
                user=mastery.user,
                lesson__content_skills__skill=mastery.skill
            ).order_by('timestamp')
            
            if events.count() < 3:
                continue
            
            # Calculate features
            total_events = events.count()
            correct_events = events.filter(detail__correct=True).count()
            total_time = sum(e.detail.get('time_spent', 0) for e in events)
            days_since_last = (timezone.now() - mastery.last_update).days
            
            training_data.append({
                'practice_count': mastery.practice_count,
                'correct_count': mastery.correct_count,
                'time_spent': total_time,
                'days_since_last': days_since_last,
                'mastery': mastery.mastery
            })
        
        if len(training_data) < 100:
            logger.warning("Insufficient training data, skipping model training")
            return
        
        # Prepare training data
        X = np.array([
            [d['practice_count'], d['correct_count'], d['time_spent'], d['days_since_last']]
            for d in training_data
        ])
        y = np.array([d['mastery'] for d in training_data])
        
        # Split and train
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
        logger.info(f"Model trained: R² train={train_score:.3f}, test={test_score:.3f}")
        
        # Save model
        model_path = os.path.join('/tmp', 'mastery_prediction_model.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        logger.info(f"Model saved to {model_path}")
        
    except Exception as e:
        logger.error(f"Model training failed: {str(e)}")


@shared_task
def batch_update_skill_decay():
    """
    Periodic task to apply HLR decay to all skill masteries.
    Should be run daily.
    """
    try:
        from .models import UserSkillMastery
        from .utils import apply_hlr_decay
        
        logger.info("Starting batch skill decay update...")
        
        masteries = UserSkillMastery.objects.all()
        updated_count = 0
        
        for mastery in masteries:
            days_since = (timezone.now() - mastery.last_update).days
            
            if days_since > 0:
                # Apply decay
                decayed_mastery = apply_hlr_decay(
                    mastery.mastery,
                    mastery.half_life_days,
                    days_since
                )
                
                # Only update if significant change (> 5%)
                if abs(decayed_mastery - mastery.mastery) > 0.05:
                    mastery.mastery = decayed_mastery
                    mastery.save(update_fields=['mastery'])
                    updated_count += 1
        
        logger.info(f"Updated decay for {updated_count} skill masteries")
        
    except Exception as e:
        logger.error(f"Batch decay update failed: {str(e)}")


@shared_task
def generate_path_with_openai(user_id: str, course_id: str, context: dict):
    """
    Generate advanced learning path using OpenAI API (optional enhancement).
    
    Args:
        user_id: User UUID
        course_id: Course UUID
        context: Dict with weak_skills, strong_skills, preferences
    """
    try:
        from openai import OpenAI
        from django.conf import settings
        
        if not hasattr(settings, 'OPENAI_API_KEY'):
            logger.warning("OpenAI API key not configured, falling back to rule-based")
            return
        
        user = User.objects.get(id=user_id)
        
        # Prepare prompt
        prompt = f"""
        Generate a personalized learning path for a primary school student.
        
        Student Profile:
        - Weak skills: {', '.join(context.get('weak_skills', []))}
        - Strong skills: {', '.join(context.get('strong_skills', []))}
        - Learning style: {context.get('learning_style', 'mixed')}
        - Difficulty preference: {context.get('difficulty_preference', 'adaptive')}
        
        Generate a sequence of 10 lessons that:
        1. Addresses weak skills progressively
        2. Respects prerequisite dependencies
        3. Maintains engagement with varied difficulty
        4. Builds on strong skills where appropriate
        
        Return JSON format: [{{"lesson_topic": "...", "skills": [...], "difficulty": "...", "rationale": "..."}}]
        """
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert education AI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse response and create path
        ai_suggestions = response.choices[0].message.content
        
        logger.info(f"Generated OpenAI path for user {user_id}: {ai_suggestions}")
        
        # Store in metadata for review
        from .models import LearningPath
        LearningPath.objects.filter(student=user, course_id=course_id).update(
            metadata={'ai_suggestions': ai_suggestions}
        )
        
    except Exception as e:
        logger.error(f"OpenAI path generation failed: {str(e)}")
