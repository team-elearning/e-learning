from django.urls import path

from quiz.api.views.exam_view import InstructorExamListView, InstructorExamDetailView, AdminExamDetailView, AdminExamListView
from quiz.api.views.practice_view import InstructorPracticeListView, InstructorPracticeDetailView, AdminPracticeDetailView, AdminPracticeListView
from quiz.api.views.parse_view import QuizParseToolView



urlpatterns = [
    path('tools/quiz-parser/', QuizParseToolView.as_view(), name='quiz-parse'),

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


    # # USER
    # # STUDENT - PRE-FLIGHT
    # # Lấy thông tin bài thi + trạng thái (đã làm bao nhiêu lần, có được thi tiếp không)
    # path('student/quizzes/<uuid:pk>/info/', StudentQuizInfoView.as_view(), name='student-quiz-info'),

    # # BẮT ĐẦU HOẶC LÀM TIẾP (Start/Resume)
    # # POST: Tạo lượt làm bài mới hoặc trả về lượt đang dang dở
    # path('student/quizzes/<uuid:pk>/attempt/', StudentQuizAttemptStartView.as_view(), name='student-quiz-attempt-start'),

    # # STUDENT - LÀM BÀI (TEST TAKING)
    # # GET: Lấy chi tiết đề thi (câu hỏi, thời gian còn lại, các câu trả lời đã lưu)
    # path('student/attempts/<uuid:pk>/', StudentAttemptDetailView.as_view(), name='student-attempt-detail'),

    # # POST: Lưu câu trả lời (Auto-save) & Đánh dấu (Flag)
    # path('student/attempts/<uuid:pk>/save-answer/', StudentAttemptSaveAnswerView.as_view(), name='student-attempt-save-answer'),

    # # POST: NỘP BÀI (SUBMIT)
    # path('student/attempts/<uuid:pk>/submit/', StudentAttemptSubmitView.as_view(), name='student-attempt-submit'),
    
    # # GET: XEM KẾT QUẢ (RESULT)
    # path('student/attempts/<uuid:pk>/result/', StudentAttemptResultView.as_view(), name='student-attempt-result'),
]