# content/api/urls.py
from django.urls import path

from content.api import views
from content.api.views.category_view import PublicCategoryListView, PublicCategoryDetailView, AdminCategoryListView, AdminCategoryDetailView
from content.api.views.course_view import PublicCourseListView, PublicCourseDetailView, CourseEnrollView, AdminCourseListCreateView, AdminCourseDetailView, AdminCoursePublishView, AdminCourseUnpublishView, InstructorCourseListCreateView, InstructorCourseDetailView, InstructorCoursePublishView, InstructorCourseUnpublishView
from content.api.views.subject_view import AdminSubjectListView, AdminSubjectDetailView
from content.api.views.module_view import PublicModuleDetailView, PublicModuleListView, InstructorModuleDetailView, InstructorModuleListCreateView, InstructorModuleReorderView, AdminModuleDetailView, AdminModuleListCreateView, AdminModuleReorderView
from content.api.views.lesson_view import PublicLessonListView, PublicLessonDetailView, InstructorLessonDetailView, InstructorLessonListView, InstructorLessonReorderView, AdminLessonDetailView, AdminLessonListView, AdminModuleLessonView, LessonContentView, InstructorLessonPreviewView, AdminLessonPreviewView
from content.api.views.lesson_version_view import AdminLessonVersionDetailView, AdminLessonVersionListCreateView, AdminLessonVersionSetStatusView, InstructorLessonVersionDetailView, InstructorLessonVersionListCreateView, InstructorLessonVersionSetStatusView



urlpatterns = [
    # Category
    path("categories/", PublicCategoryListView.as_view(), name="public-category-list"),
    path("categories/<uuid:id>/", PublicCategoryDetailView.as_view(), name="public-category-detail"),

    # Course
    path('courses/', PublicCourseListView.as_view(), name='public-course-list'),
    path('courses/<uuid:pk>/', PublicCourseDetailView.as_view(), name='public-course-detail'),
    path('courses/<uuid:course_id>/enroll/', CourseEnrollView.as_view(), name='course-enroll'),

    # Module
    path('courses/<uuid:course_id>/modules/', PublicModuleListView.as_view(), name='public-course-list'),
    path('modules/<uuid:pk>/', PublicModuleDetailView.as_view(), name='public-course-detail'),

    # Lesson
    path('modules/<uuid:module_id>/lessons/', PublicLessonListView.as_view(), name='public-lesson-list'),
    path('lessons/<uuid:pk>/', PublicLessonDetailView.as_view(), name='public-lesson-detail'),

    # Lesson - content
    path('lessons/<uuid:lesson_id>/content/', LessonContentView.as_view(), name='lesson-content'),

    # ---------------------------- ADMIN ---------------------------------------
    path("admin/categories/", AdminCategoryListView.as_view(), name="admin-category-list"),
    path("admin/categories/<uuid:id>/", AdminCategoryDetailView.as_view(), name="admin-category-detail"),

    path('admin/subjects/', AdminSubjectListView.as_view(), name='admin-subject-list'),
    path('admin/subjects/<uuid:pk>/', AdminSubjectDetailView.as_view(), name='admin-subject-detail'),

    path('admin/courses/', AdminCourseListCreateView.as_view(), name='admin-course-list-create'),
    path('admin/courses/<uuid:course_id>', AdminCourseDetailView.as_view(), name='admin-course-detail'),
    path('admin/courses/<uuid:course_id>/publish/', AdminCoursePublishView.as_view(), name='admin-course-publish'),
    path('admin/courses/<uuid:course_id>/unpublish/', AdminCourseUnpublishView.as_view(), name='admin-course-unpublish'),

    path('admin/courses/<uuid:course_id>/modules/', AdminModuleListCreateView.as_view(), name='admin-module-list'),
    path('admin/modules/<uuid:pk>/', AdminModuleDetailView.as_view(), name='admin-module-detail'),
    path('admin/courses/<uuid:course_id>/modules/reorder/', AdminModuleReorderView.as_view(), name='admin-module-reorder'),

    path('admin/modules/<uuid:module_id>/lessons/', AdminModuleLessonView.as_view(), name='admin-module-lesson-list-create'),
    path('admin/lessons/', AdminLessonListView.as_view(), name='admin-lesson-list-all'),
    path('admin/lessons/<uuid:pk>/', AdminLessonDetailView.as_view(), name='admin-lesson-detail'),

    path('admin/lessons/<uuid:lesson_id>/preview/', AdminLessonPreviewView.as_view(), name='admin-lesson-preview'),

    path('admin/lessons/<uuid:lesson_id>/versions/', AdminLessonVersionListCreateView.as_view(), name='admin-lesson-version-list-create'),
    path('admin/lesson-versions/<uuid:pk>/', AdminLessonVersionDetailView.as_view(), name='admin-lesson-version-detail'),
    path('admin/lesson-versions/<uuid:pk>/set_status/', AdminLessonVersionSetStatusView.as_view(), name='admin-lesson-version-set-status'),

    # ---------------------------- INSTRUCTOR ---------------------------------------
    path('instructor/courses/', InstructorCourseListCreateView.as_view(), name='instructor-course-list-create'),
    path('instructor/courses/<uuid:pk>/', InstructorCourseDetailView.as_view(), name='instructor-course-detail'),
    path('instructor/courses/<uuid:course_id>/publish/', InstructorCoursePublishView.as_view(), name='instructor-course-publish'),
    path('instructor/courses/<uuid:course_id>/unpublish/', InstructorCourseUnpublishView.as_view(), name='instructor-course-unpublish'),

    path('instructor/courses/<uuid:course_id>/modules/', InstructorModuleListCreateView.as_view(), name='instructor-module-list'),
    path('instructor/modules/<uuid:pk>/', InstructorModuleDetailView.as_view(), name='instructor-module-detail'),
    path('instructor/courses/<uuid:course_id>/modules/reorder/', InstructorModuleReorderView.as_view(), name='instructor-module-reorder'),

    path('instructor/modules/<uuid:module_id>/lessons/', InstructorLessonListView.as_view(), name='instructor-lesson-list-create'),
    path('instructor/lessons/<uuid:pk>/', InstructorLessonDetailView.as_view(), name='instructor-lesson-detail'),
    path('instructor/modules/<uuid:module_id>/lessons/reorder/', InstructorLessonReorderView.as_view(), name='instructor-lesson-reorder'),

    path('instructor/lessons/<uuid:lesson_id>/preview/', InstructorLessonPreviewView.as_view(), name='instructor-lesson-preview'),

    path('instructor/lessons/<uuid:lesson_id>/versions/', InstructorLessonVersionListCreateView.as_view(), name='instructor-lesson-version-list-create'),
    path('instructor/lesson-versions/<uuid:pk>/', InstructorLessonVersionDetailView.as_view(), name='instructor-lesson-version-detail'),
    path('instructor/lesson-versions/<uuid:pk>/set_status/', InstructorLessonVersionSetStatusView.as_view(), name='instructor-lesson-version-set-status'),

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