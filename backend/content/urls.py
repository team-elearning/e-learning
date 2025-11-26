# content/api/urls.py
from django.urls import path

# from content.api.views.category_view import PublicCategoryListView, PublicCategoryDetailView, AdminCategoryListView, AdminCategoryDetailView
from content.api.views.course_view import PublicCourseListView, PublicCourseDetailView, AdminCourseListCreateView, AdminCourseDetailView, InstructorCourseListCreateView, InstructorCourseDetailView, AdminCoursePublishView, AdminCourseUnpublishView, InstructorCoursePublishView, InstructorCourseUnpublishView
from content.api.views.subject_view import AdminSubjectListView
# from content.api.views.module_view import PublicModuleDetailView, PublicModuleListView, InstructorModuleDetailView, InstructorModuleListCreateView, InstructorModuleReorderView, AdminModuleDetailView, AdminModuleListCreateView, AdminModuleReorderView
# from content.api.views.lesson_view import PublicLessonListView, PublicLessonDetailView, InstructorLessonDetailView, InstructorLessonListView, InstructorLessonReorderView, AdminLessonDetailView, AdminLessonListView, AdminModuleLessonView, LessonContentView, InstructorLessonPreviewView, AdminLessonPreviewView
# from content.api.views.content_block_view import PublicLessonBlockListView, AdminContentBlockDetailView, AdminContentBlockReorderView, AdminLessonVersionContentBlockListView, InstructorContentBlockDetailView, InstructorContentBlockReorderView, InstructorLessonVersionContentBlockListView
from quiz.api.views.quiz_course_view import AdminQuizListView, IntructorQuizDetailView, AdminQuizDetailView, QuizCourseAttemptView
from content.api.views.enrollment_view import CourseEnrollView, MyEnrolledCourseListView, InstructorCourseParticipantListView, InstructorCourseParticipantDetailView, AdminCourseParticipantListView, AdminCourseParticipantDetailView



urlpatterns = [
    # # Category
    # path("categories/", PublicCategoryListView.as_view(), name="public-category-list"),
    # path("categories/<uuid:id>/", PublicCategoryDetailView.as_view(), name="public-category-detail"),

    # # Course
    # path('courses/', PublicCourseListView.as_view(), name='public-course-list'),
    # path('courses/<uuid:pk>/', PublicCourseDetailView.as_view(), name='public-course-detail'),
    # path('courses/<uuid:course_id>/enroll/', CourseEnrollView.as_view(), name='course-enroll'),

    # # Module
    # path('courses/<uuid:course_id>/modules/', PublicModuleListView.as_view(), name='public-course-list'),
    # path('modules/<uuid:pk>/', PublicModuleDetailView.as_view(), name='public-course-detail'),

    # # Lesson
    # path('modules/<uuid:module_id>/lessons/', PublicLessonListView.as_view(), name='public-lesson-list'),
    # path('lessons/<uuid:pk>/', PublicLessonDetailView.as_view(), name='public-lesson-detail'),

    # # Lesson - content
    # path('lessons/<uuid:lesson_id>/content/', LessonContentView.as_view(), name='lesson-content'),

    # # Content - block
    # path('lesson-versions/<uuid:lesson_version_id>/blocks/', PublicLessonBlockListView.as_view(), name='public-block-list'),

    path('courses/', PublicCourseListView.as_view(), name='public-course-list'),
    path('courses/<uuid:pk>/enroll/', CourseEnrollView.as_view(), name='public-course-enroll'),
    path('courses/<uuid:pk>/unenroll/', CourseEnrollView.as_view(), name='public-course-unenroll'),
    path('my-courses/', MyEnrolledCourseListView.as_view(), name='public-course-list'),
    path('courses/<uuid:pk>/', PublicCourseDetailView.as_view(), name='public-course-detail'),


    # # ---------------------------- ADMIN ---------------------------------------
    # path("admin/categories/", AdminCategoryListView.as_view(), name="admin-category-list"),
    # path("admin/categories/<uuid:id>/", AdminCategoryDetailView.as_view(), name="admin-category-detail"),

    # path('admin/subjects/', AdminSubjectListView.as_view(), name='admin-subject-list'),
    # path('admin/subjects/<uuid:pk>/', AdminSubjectDetailView.as_view(), name='admin-subject-detail'),

    # path('admin/courses/', AdminCourseListCreateView.as_view(), name='admin-course-list-create'),
    # path('admin/courses/<uuid:course_id>', AdminCourseDetailView.as_view(), name='admin-course-detail'),
    # path('admin/courses/<uuid:course_id>/publish/', AdminCoursePublishView.as_view(), name='admin-course-publish'),
    # path('admin/courses/<uuid:course_id>/unpublish/', AdminCourseUnpublishView.as_view(), name='admin-course-unpublish'),

    # path('admin/courses/<uuid:course_id>/modules/', AdminModuleListCreateView.as_view(), name='admin-module-list'),
    # path('admin/modules/<uuid:pk>/', AdminModuleDetailView.as_view(), name='admin-module-detail'),
    # path('admin/courses/<uuid:course_id>/modules/reorder/', AdminModuleReorderView.as_view(), name='admin-module-reorder'),

    # path('admin/modules/<uuid:module_id>/lessons/', AdminModuleLessonView.as_view(), name='admin-module-lesson-list-create'),
    # path('admin/lessons/', AdminLessonListView.as_view(), name='admin-lesson-list-all'),
    # path('admin/lessons/<uuid:pk>/', AdminLessonDetailView.as_view(), name='admin-lesson-detail'),

    # path('admin/lessons/<uuid:lesson_id>/preview/', AdminLessonPreviewView.as_view(), name='admin-lesson-preview'),

    # path('admin/lesson-versions/<uuid:lesson_version_id>/blocks/', AdminLessonVersionContentBlockListView.as_view(), name='admin-lesson-block-list'),
    # path('admin/lesson-versions/<uuid:lesson_version_id>/blocks/reorder/', AdminContentBlockReorderView.as_view(), name='admin-block-reorder'),
    # path('admin/content-blocks/<uuid:pk>/', AdminContentBlockDetailView.as_view(), name='admin-block-detail'),

    path('admin/courses/', AdminCourseListCreateView.as_view(), name='admin-course-list-create'),
    path('admin/courses/<uuid:pk>/', AdminCourseDetailView.as_view(), name='admin-course-detail'),
    path('admin/courses/<uuid:pk>/publish/', AdminCoursePublishView.as_view(), name='admin-course-public'),
    path('admin/courses/<uuid:pk>/unpublish/', AdminCourseUnpublishView.as_view(), name='admin-course-unpublic'),

    path('admin/quizzes/', AdminQuizListView.as_view(), name='admin-quiz-list'),
    path('admin/quizzes/<uuid:pk>/', AdminQuizDetailView.as_view(), name='admin-quiz-detail'),

    path('admin/subjects/', AdminSubjectListView.as_view(), name='admin-subject-list'),

    path('admin/courses/<uuid:pk>/users/', AdminCourseParticipantListView.as_view(), name='admin-course-participant'),
    path('admin/courses/<uuid:pk>/users/<uuid:user_id>/', AdminCourseParticipantListView.as_view(), name='admin-course-participant'),

    # # ---------------------------- INSTRUCTOR ---------------------------------------
    path('instructor/courses/', InstructorCourseListCreateView.as_view(), name='instructor-course-list-create'),
    path('instructor/courses/<uuid:pk>/', InstructorCourseDetailView.as_view(), name='instructor-course-detail'),
    path('instructor/courses/<uuid:pk>/publish/', InstructorCoursePublishView.as_view(), name='instructor-course-public'),
    path('instructor/courses/<uuid:pk>/unpublish/', InstructorCourseUnpublishView.as_view(), name='instructor-course-unpublic'),
    
    path('instructor/quizzes/<uuid:pk>/', IntructorQuizDetailView.as_view(), name='instructor-quiz-detail'),

    path('instructor/courses/<uuid:pk>/users/', InstructorCourseParticipantListView.as_view(), name='instructor-course-participant'),
    path('instructor/courses/<uuid:pk>/users/<uuid:user_id>/', AdminCourseParticipantDetailView.as_view(), name='instructor-course-participant'),


    # path('instructor/courses/<uuid:course_id>/publish/', InstructorCoursePublishView.as_view(), name='instructor-course-publish'),
    # path('instructor/courses/<uuid:course_id>/unpublish/', InstructorCourseUnpublishView.as_view(), name='instructor-course-unpublish'),

    # path('instructor/courses/<uuid:course_id>/modules/', InstructorModuleListCreateView.as_view(), name='instructor-module-list'),
    # path('instructor/modules/<uuid:pk>/', InstructorModuleDetailView.as_view(), name='instructor-module-detail'),
    # path('instructor/courses/<uuid:course_id>/modules/reorder/', InstructorModuleReorderView.as_view(), name='instructor-module-reorder'),

    # path('instructor/modules/<uuid:module_id>/lessons/', InstructorLessonListView.as_view(), name='instructor-lesson-list-create'),
    # path('instructor/lessons/<uuid:pk>/', InstructorLessonDetailView.as_view(), name='instructor-lesson-detail'),
    # path('instructor/modules/<uuid:module_id>/lessons/reorder/', InstructorLessonReorderView.as_view(), name='instructor-lesson-reorder'),

    # path('instructor/lessons/<uuid:lesson_id>/preview/', InstructorLessonPreviewView.as_view(), name='instructor-lesson-preview'),

    # path('lesson-versions/<uuid:lesson_version_id>/blocks/', InstructorLessonVersionContentBlockListView.as_view(), name='instructor-lesson-block-list'),   
    # path('lesson-versions/<uuid:lesson_version_id>/blocks/reorder/', InstructorContentBlockReorderView.as_view(), name='instructor-block-reorder'),    
    # path('content-blocks/<uuid:pk>/', InstructorContentBlockDetailView.as_view(), name='instructor-block-detail'),





    # # ---------------------------
    # # Search & Utility
    # # ---------------------------
    # path("search/", views.SearchView.as_view(), name="content-search"),
    # path("me/courses/", views.MyCoursesListView.as_view(), name="my-courses"),
    # path("me/explorations/", views.MyExplorationsListView.as_view(), name="my-explorations"),

    # # ---------------------------
    # # Categories & Tags
    # # ---------------------------
    # path("categories/", views.CategoryListCreateView.as_view(), name="category-list"),
    # path("categories/<uuid:pk>/", views.CategoryDetailView.as_view(), name="category-detail"),
    # path("tags/", views.TagListCreateView.as_view(), name="tag-list"),
    # path("tags/<uuid:pk>/", views.TagDetailView.as_view(), name="tag-detail"),

    # # ---------------------------
    # # Subject
    # # ---------------------------
    # path("subjects/", views.SubjectListCreateView.as_view(), name="subject-list"),
    # path("subjects/<uuid:pk>/", views.SubjectDetailView.as_view(), name="subject-detail"),

    # # ---------------------------
    # # Course
    # # ---------------------------
    # path("courses/", views.CourseListCreateView.as_view(), name="course-list"),
    # path("courses/<uuid:pk>/", views.CourseDetailView.as_view(), name="course-detail"),
    # path("courses/<uuid:course_id>/publish/", views.CoursePublishView.as_view(), name="course-publish"),
    # path("courses/<uuid:course_id>/unpublish/", views.CourseUnpublishView.as_view(), name="course-unpublish"),
    # path("courses/<uuid:course_id>/enroll/", views.CourseEnrollView.as_view(), name="course-enroll"),

    # # ---------------------------
    # # Module (nested under a Course)
    # # ---------------------------
    # path("courses/<uuid:course_id>/modules/", views.ModuleListCreateView.as_view(), name="module-list"),
    # path("modules/<uuid:pk>/", views.ModuleDetailView.as_view(), name="module-detail"),
    # path("courses/<uuid:course_id>/modules/reorder/", views.ModuleReorderView.as_view(), name="module-reorder"),

    # # ---------------------------
    # # Lesson (nested under a Module)
    # # ---------------------------
    # path("modules/<uuid:module_id>/lessons/", views.LessonListCreateView.as_view(), name="lesson-list"),
    # path("lessons/<uuid:pk>/", views.LessonDetailView.as_view(), name="lesson-detail"),
    # path("lessons/<uuid:lesson_id>/content/", views.LessonContentView.as_view(), name="lesson-content"),
    # path("modules/<uuid:module_id>/lessons/reorder/", views.LessonReorderView.as_view(), name="lesson-reorder"),

    # # ---------------------------
    # # Lesson Versions (nested under a Lesson)
    # # ---------------------------
    # path("lessons/<uuid:lesson_id>/versions/", views.LessonVersionListCreateView.as_view(), name="lessonversion-list"),
    # path("lesson-versions/<uuid:pk>/", views.LessonVersionDetailView.as_view(), name="lessonversion-detail"),
    # path("versions/<uuid:version_id>/set_status/", views.LessonVersionSetStatusView.as_view(), name="lessonversion-set-status"),
    # path("lessons/<uuid:lesson_id>/preview/", views.LessonVersionPreviewView.as_view(), name="lessonversion-preview"),

    # # ---------------------------
    # # Content Blocks (nested under a Lesson Version)
    # # ---------------------------
    # path("lesson-versions/<uuid:lesson_version_id>/blocks/", views.ContentBlockListCreateView.as_view(), name="contentblock-list"),
    # path("content-blocks/<uuid:pk>/", views.ContentBlockDetailView.as_view(), name="contentblock-detail"),
    # path("lesson-versions/<uuid:lesson_version_id>/blocks/reorder/", views.ContentBlockReorderView.as_view(), name="contentblock-reorder"),

    # # ---------------------------
    # # Explorations (Interactive Lessons)
    # # ---------------------------
    # path("explorations/", views.ExplorationListCreateView.as_view(), name="exploration-list"),
    # path("explorations/<str:id>/", views.ExplorationDetailView.as_view(), name="exploration-detail"),
    # path("explorations/<str:id>/player/", views.ExplorationPlayerView.as_view(), name="exploration-player"),
    # path("explorations/<str:id>/editor/", views.ExplorationDetailView.as_view(), name="exploration-editor"),
    # path("explorations/<str:exploration_id>/publish/", views.ExplorationPublishView.as_view(), name="exploration-publish"),
    # path("explorations/<str:exploration_id>/unpublish/", views.ExplorationUnpublishView.as_view(), name="exploration-unpublish"),
    # path("explorations/<str:exploration_id>/media/upload/", views.ExplorationMediaUploadView.as_view(), name="exploration-media-upload"),
]