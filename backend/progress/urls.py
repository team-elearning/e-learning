from django.urls import path

from progress.api.views.heart_beat_view import BlockInteractionHeartbeatView, BlockCompletionView, CourseResumeView
from progress.api.views.quiz_attempt_view import QuizAttemptInitView, QuizAttemptFinishView
from progress.api.views.question_attempt_view import AttemptQuestionDetailView, AttemptQuestionSaveDraftView, AttemptQuestionSubmitView



urlpatterns = [
    # Tracking
    path('tracking/heartbeat/blocks/<uuid:block_id>/', BlockInteractionHeartbeatView.as_view(), name='block-heartbeat'),
    path('tracking/complete/', BlockCompletionView.as_view(), name='tracking-completion'),

    path('tracking/resume/<uuid:course_id>/', CourseResumeView.as_view(), name='tracking-resume'),
    
    # Attempt 
    # Quiz
    path('quizzes/<uuid:quiz_id>/attempt/', QuizAttemptInitView.as_view(), name='quiz-attempt-init'),
    path('quizzes/attempts/<uuid:attempt_id>/finish/', QuizAttemptFinishView.as_view(), name='quiz-attempt-finish'),

    # Question
    path('attempts/<uuid:attempt_id>/questions/<uuid:question_id>/', AttemptQuestionDetailView.as_view(), name='question-attempt-detail'),
    path('attempts/<uuid:attempt_id>/questions/<uuid:question_id>/draft/', AttemptQuestionSaveDraftView.as_view(), name='question-attempt-draft'),
    path('attempts/<uuid:attempt_id>/questions/<uuid:question_id>/submit/', AttemptQuestionSubmitView.as_view(), name='question-attempt-submit'),
]