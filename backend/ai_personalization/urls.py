# from django.urls import path
# from .views import LearningEventView, NextRecommendationView, RecommendationFeedbackView

# urlpatterns = [
#     path('events/', LearningEventView.as_view(), name='learning-event'),
#     path('personalization/next/', NextRecommendationView.as_view(), name='personalization-next'),
#     path('personalization/feedback/', RecommendationFeedbackView.as_view(), name='personalization-feedback'),
# ]



# ai_personalization/urls.py
"""
URL configuration for AI personalization API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LearningPathViewSet, RecommendationViewSet, LearningEventViewSet,
    UserSkillMasteryViewSet, PersonalizationAnalyticsView, SkillGraphView
)



app_name = 'ai_personalization'

router = DefaultRouter()
router.register(r'paths', LearningPathViewSet, basename='learning-path')
router.register(r'recommendations', RecommendationViewSet, basename='recommendation')
router.register(r'events', LearningEventViewSet, basename='learning-event')
router.register(r'mastery', UserSkillMasteryViewSet, basename='skill-mastery')

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/', PersonalizationAnalyticsView.as_view(), name='analytics'),
    path('skill-graph/', SkillGraphView.as_view(), name='skill-graph'),
]