from django.urls import path

from progress.api.views.heart_beat_view import BlockInteractionHeartbeatView, BlockCompletionView, CourseResumeView
from progress.api.views.quiz_progress_view import StartQuizAttemptView



urlpatterns = [
    path('tracking/heartbeat/', BlockInteractionHeartbeatView.as_view(), name='tracking-heartbeat'),
    path('tracking/complete/', BlockCompletionView.as_view(), name='tracking-completion'),

    path('tracking/resume/<uuid:course_id>/', CourseResumeView.as_view(), name='tracking-resume'),

    path('tracking/quiz/', StartQuizAttemptView.as_view(), name='quiz-start-attempt'),
]