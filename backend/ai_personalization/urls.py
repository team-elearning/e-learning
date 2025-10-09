from django.urls import path
from .views import LearningEventView, NextRecommendationView, RecommendationFeedbackView

urlpatterns = [
    path('events/', LearningEventView.as_view(), name='learning-event'),
    path('personalization/next/', NextRecommendationView.as_view(), name='personalization-next'),
    path('personalization/feedback/', RecommendationFeedbackView.as_view(), name='personalization-feedback'),
]