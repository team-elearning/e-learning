from django.urls import path
from quiz.api.views.exam_view import InstructorExamListView, InstructorExamDetailView

urlpatterns = [
    path('instructor/exams/', InstructorExamListView.as_view(), name='instructor-exam-list-create'),
    path('instructor/exams/<uuid:pk>/', InstructorExamDetailView.as_view(), name='instructor-exam-detail'),
]