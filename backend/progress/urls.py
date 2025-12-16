from django.urls import path

from progress.api.views.heart_beat_view import BlockInteractionHeartbeatView, BlockCompletionView, CourseResumeView
from progress.api.views.quiz_attempt_view import QuizAttemptInitView
from progress.api.views.question_attempt_view import AttemptQuestionDetailView



urlpatterns = [
    # Tracking
    path('tracking/heartbeat/', BlockInteractionHeartbeatView.as_view(), name='tracking-heartbeat'),
    path('tracking/complete/', BlockCompletionView.as_view(), name='tracking-completion'),

    path('tracking/resume/<uuid:course_id>/', CourseResumeView.as_view(), name='tracking-resume'),
    
    # Attempt
    path('quizzes/<uuid:quiz_id>/attempt/', QuizAttemptInitView.as_view(), name='quiz-attempt-init'),

    path('attempts/<uuid:attempt_id>/questions/<uuid:question_id>/', AttemptQuestionDetailView.as_view(), name='question-attempt-detail')
]