from django.urls import path

from quiz.api.views.exam_view import InstructorExamListView, InstructorExamDetailView, AdminExamDetailView, AdminExamListView
from quiz.api.views.practice_view import InstructorPracticeListView, InstructorPracticeDetailView, AdminPracticeDetailView, AdminPracticeListView
from quiz.api.views.parse_view import QuizParseToolView
from quiz.api.views.quiz_user_view import QuizInfoView, QuizAttemptStartView, AttemptDetailView, AttemptSaveAnswerView, AttemptSubmitView, AttemptResultView, QuizListView



urlpatterns = [
    # USER
    path('exam/<uuid:pk>/info/', QuizInfoView.as_view(), name='student-quiz-info'),
    path('exam/<uuid:pk>/attempt/', QuizAttemptStartView.as_view(), name='quiz-attempt-start'),
    path('attempts/<uuid:pk>/', AttemptDetailView.as_view(), name='student-attempt-detail'),
    path('attempts/<uuid:pk>/save/', AttemptSaveAnswerView.as_view(), name='student-attempt-save-answer'),
    path('attempts/<uuid:pk>/submit/', AttemptSubmitView.as_view(), name='student-attempt-submit'),
    path('attempts/<uuid:pk>/result/', AttemptResultView.as_view(), name='student-attempt-result'),
    path('', QuizListView.as_view(), name='list-exam-practice'),

    path('tools/quiz-parser/', QuizParseToolView.as_view(), name='quiz-parse'), # Cho instructor chủ yếu

    # INSTRUCTOR
    path('instructor/exams/', InstructorExamListView.as_view(), name='instructor-exam-list-create'),
    path('instructor/exams/<uuid:pk>/', InstructorExamDetailView.as_view(), name='instructor-exam-detail'),

    path('instructor/practices/', InstructorPracticeListView.as_view(), name='instructor-practice-list-create'),
    path('instructor/practices/<uuid:pk>/', InstructorPracticeDetailView.as_view(), name='instructor-practice-detail'),


    # ADMIN
    path('admin/exams/', AdminExamListView.as_view(), name='admin-exam-list-create'),
    path('admin/exams/<uuid:pk>/', AdminExamDetailView.as_view(), name='admin-exam-detail'),

    path('admin/practices/', AdminPracticeListView.as_view(), name='admin-practice-list-create'),
    path('admin/practices/<uuid:pk>/', AdminPracticeDetailView.as_view(), name='admin-practice-detail'),
]