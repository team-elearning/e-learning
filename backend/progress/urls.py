from django.urls import path
from progress.api.views.heart_beat_view import BlockInteractionHeartbeatView



urlpatterns = [
    path('tracking/heartbeat/', BlockInteractionHeartbeatView.as_view(), name='tracking-heartbeat'),
]