from django.urls import path
from quiz.api.views.exam_view import InstructorExamListView, InstructorExamDetailView

urlpatterns = [
    # ... các url khác
    
    # Quản lý danh sách bài thi (List & Create)
    path('instructor/exams/', InstructorExamListView.as_view(), name='instructor-exam-list-create'),
    
    # # Quản lý chi tiết bài thi (Detail, Update, Delete)
    # path('instructor/exams/<uuid:pk>/', InstructorExamDetailView.as_view(), name='instructor-exam-detail'),
]