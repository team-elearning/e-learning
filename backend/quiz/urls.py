from django.urls import path

from quiz.api.views.exam_view import InstructorExamListView, InstructorExamDetailView, AdminExamDetailView, AdminExamListView
from quiz.api.views.practice_view import InstructorPracticeListView, InstructorPracticeDetailView, AdminPracticeDetailView, AdminPracticeListView
from quiz.api.views.parse_view import QuizParseToolView



urlpatterns = [
    # INSTRUCTOR
    path('instructor/exams/', InstructorExamListView.as_view(), name='instructor-exam-list-create'),
    path('instructor/exams/<uuid:pk>/', InstructorExamDetailView.as_view(), name='instructor-exam-detail'),

    path('instructor/practices/', InstructorPracticeListView.as_view(), name='instructor-practice-list-create'),
    path('instructor/practices/<uuid:pk>/', InstructorPracticeDetailView.as_view(), name='instructor-practice-detail'),

    path('tools/quiz-parser/', QuizParseToolView.as_view(), name='quiz-parse'),


    # ADMIN
    path('admin/exams/', AdminExamListView.as_view(), name='admin-exam-list-create'),
    path('admin/exams/<uuid:pk>/', AdminExamDetailView.as_view(), name='admin-exam-detail'),

    path('admin/practices/', AdminPracticeListView.as_view(), name='admin-practice-list-create'),
    path('admin/practices/<uuid:pk>/', AdminPracticeDetailView.as_view(), name='admin-practice-detail'),
]