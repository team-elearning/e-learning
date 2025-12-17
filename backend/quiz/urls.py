from django.urls import path

from quiz.api.views.exam_view import InstructorExamListView, InstructorExamDetailView, AdminExamDetailView, AdminExamListView
from quiz.api.views.practice_view import InstructorPracticeListView, InstructorPracticeDetailView, AdminPracticeDetailView, AdminPracticeListView
from quiz.api.views.parse_view import QuizParseToolView
# from quiz.api.views.quiz_user_view import QuizAttemptStartView, AttemptDetailView, AttemptSaveAnswerView, AttemptSubmitView, AttemptResultView, QuizListView
from quiz.api.views.quiz_course_view import IntructorQuizCourseDetailView
from quiz.api.views.question_view import InstructorQuestionListView, InstructorQuestionDetailView



urlpatterns = [
    # USER

    # path('exam/<uuid:pk>/info/', QuizInfoView.as_view(), name='student-quiz-info'),
    # path('exam/<uuid:pk>/attempt/', QuizAttemptStartView.as_view(), name='quiz-attempt-start'),
    # path('attempts/<uuid:pk>/', AttemptDetailView.as_view(), name='student-attempt-detail'),
    # path('attempts/<uuid:pk>/save/', AttemptSaveAnswerView.as_view(), name='student-attempt-save-answer'),
    # path('attempts/<uuid:pk>/submit/', AttemptSubmitView.as_view(), name='student-attempt-submit'),
    # path('attempts/<uuid:pk>/result/', AttemptResultView.as_view(), name='student-attempt-result'),
    # path('', QuizListView.as_view(), name='list-exam-practice'),

    path('tools/quiz-parser/', QuizParseToolView.as_view(), name='quiz-parse'), # Cho instructor chủ yếu

    # INSTRUCTOR
    # Course
    path('instructor/quizzes/<uuid:quiz_id>/', IntructorQuizCourseDetailView.as_view(), name='instructor-quiz-detail'),
    path('instructor/quizzes/<uuid:quiz_id>/questions/', InstructorQuestionListView.as_view(), name='instructor-question-list'),
    path('instructor/questions/<uuid:question_id>/', InstructorQuestionDetailView.as_view(), name='instructor-question-detail'),
    
    # # Exam
    # path('instructor/exams/', InstructorExamListView.as_view(), name='instructor-exam-list-create'),
    # path('instructor/exams/<uuid:pk>/', InstructorExamDetailView.as_view(), name='instructor-exam-detail'),

    # path('instructor/practices/', InstructorPracticeListView.as_view(), name='instructor-practice-list-create'),
    # path('instructor/practices/<uuid:pk>/', InstructorPracticeDetailView.as_view(), name='instructor-practice-detail'),


    # ADMIN
    # Course
    # path('admin/quizzes/', AdminQuizListView.as_view(), name='admin-quiz-list'),
    # path('admin/quizzes/<uuid:pk>/', AdminQuizDetailView.as_view(), name='admin-quiz-detail'),

    # path('admin/exams/', AdminExamListView.as_view(), name='admin-exam-list-create'),
    # path('admin/exams/<uuid:pk>/', AdminExamDetailView.as_view(), name='admin-exam-detail'),

    # path('admin/practices/', AdminPracticeListView.as_view(), name='admin-practice-list-create'),
    # path('admin/practices/<uuid:pk>/', AdminPracticeDetailView.as_view(), name='admin-practice-detail'),
]