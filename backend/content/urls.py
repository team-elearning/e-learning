from django.urls import path

from content.api.views.course_view import InstructorCourseListCreateView, InstructorCourseDetailView
from content.api.views.subject_view import AdminSubjectListView
from content.api.views.module_view import InstructorModuleListCreateView, InstructorModuleDetailView, InstructorModuleReorderView
from content.api.views.lesson_view import InstructorLessonListCreateView, InstructorLessonDetailView, InstructorLessonReorderView
from content.api.views.content_block_view import InstructorContentBlockListCreateView, InstructorContentBlockConvertView, InstructorContentBlockDetailView, InstructorContentBlockReorderView
from quiz.api.views.quiz_course_view import AdminQuizListView, AdminQuizDetailView, QuizCourseAttemptView, IntructorQuizCourseDetailView
from content.api.views.enrollment_view import CourseEnrollView, MyEnrolledCourseListView, InstructorCourseParticipantListView, InstructorCourseParticipantDetailView, AdminCourseParticipantListView, AdminCourseParticipantDetailView



urlpatterns = [
    # # ---------------------------- PUBLIC ---------------------------------------
    # path('courses/', PublicCourseListView.as_view(), name='public-course-list'),
    # path('courses/<uuid:pk>/enroll/', CourseEnrollView.as_view(), name='public-course-enroll'),
    # path('courses/<uuid:pk>/unenroll/', CourseEnrollView.as_view(), name='public-course-unenroll'),
    # path('my-courses/', MyEnrolledCourseListView.as_view(), name='public-course-list'),
    # path('courses/<uuid:pk>/', PublicCourseDetailView.as_view(), name='public-course-detail'),


    # # ---------------------------- ADMIN ---------------------------------------
    # path('admin/courses/', AdminCourseListCreateView.as_view(), name='admin-course-list-create'),
    # path('admin/courses/<uuid:pk>/', AdminCourseDetailView.as_view(), name='admin-course-detail'),
    # path('admin/courses/<uuid:pk>/publish/', AdminCoursePublishView.as_view(), name='admin-course-public'),
    # path('admin/courses/<uuid:pk>/unpublish/', AdminCourseUnpublishView.as_view(), name='admin-course-unpublic'),

    path('admin/subjects/', AdminSubjectListView.as_view(), name='admin-subject-list'),

    path('admin/courses/<uuid:pk>/users/', AdminCourseParticipantListView.as_view(), name='admin-course-participant'),
    path('admin/courses/<uuid:pk>/users/<uuid:user_id>/', AdminCourseParticipantListView.as_view(), name='admin-course-participant'),

    # # ---------------------------- INSTRUCTOR ---------------------------------------
    # Course
    path('instructor/courses/', InstructorCourseListCreateView.as_view(), name='instructor-course-list-create'),
    path('instructor/courses/<uuid:pk>/', InstructorCourseDetailView.as_view(), name='instructor-course-detail'),
    # path('instructor/courses/<uuid:pk>/publish/', InstructorCoursePublishView.as_view(), name='instructor-course-public'),
    # path('instructor/courses/<uuid:pk>/unpublish/', InstructorCourseUnpublishView.as_view(), name='instructor-course-unpublic'),

    # Module
    path('instructor/courses/<uuid:course_id>/modules/', InstructorModuleListCreateView.as_view(), name='instructor-module-list'),
    path('instructor/modules/<uuid:module_id>/', InstructorModuleDetailView.as_view(), name='instructor-module-detail'),
    path('instructor/courses/<uuid:course_id>/modules/reorder/', InstructorModuleReorderView.as_view(), name='instructor-module-reorder'),

    # Lesson
    path('instructor/modules/<uuid:module_id>/lessons/', InstructorLessonListCreateView.as_view(), name='instructor-lesson-list'),
    path('instructor/lessons/<uuid:lesson_id>/', InstructorLessonDetailView.as_view(), name='instructor-lesson-detail'),
    path('instructor/courses/<uuid:course_id>/modules/<uuid:module_id>/lessons/reorder/', InstructorLessonReorderView.as_view(),name='instructor-lesson-reorder'),
    
    # Content Block
    path('instructor/lessons/<uuid:lesson_id>/blocks/', InstructorContentBlockListCreateView.as_view(), name='instructor-block-list'),
    path('instructor/blocks/<uuid:block_id>/', InstructorContentBlockDetailView.as_view(), name='instructor-block-detail'),
    path('instructor/blocks/<uuid:block_id>/convert/', InstructorContentBlockConvertView.as_view(), name='instructor-block-convert'),
    path('lessons/<uuid:lesson_id>/blocks/reorder/', InstructorContentBlockReorderView.as_view(), name='instructor-block-reorder'),

    # User in course
    path('instructor/courses/<uuid:pk>/users/', InstructorCourseParticipantListView.as_view(), name='instructor-course-participant'),
    path('instructor/courses/<uuid:pk>/users/<uuid:user_id>/', InstructorCourseParticipantDetailView.as_view(), name='instructor-course-participant'),
]