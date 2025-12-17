from django.urls import path
from personalization.api.views.views import AISyncView, AIRecommendationView, UserRecommendationView



urlpatterns = [ 
    path('ai/sync/', AISyncView.as_view(), name='ai-sync'),
    path('ai/suggest/', AIRecommendationView.as_view(), name='ai-suggest'),

    path('ai/recommend-for-me/', UserRecommendationView.as_view(), name='ai-recommend-user'),
]