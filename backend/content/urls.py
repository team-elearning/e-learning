# content/api/urls.py
from django.urls import path

from content.api import views
from content.api.views import subject_view, course_view, module_view, lesson_view, lesson_version_view, content_block_view, exploration_view, exploration_state_view, exploration_transition_view

urlpatterns = [
    # ---------------------------
    # Subject
    # ---------------------------
    path("subjects/", subject_view.SubjectListCreateView.as_view(), name="subject-list"),
    path("subjects/<uuid:pk>/", subject_view.SubjectDetailView.as_view(), name="subject-detail"),

    # ---------------------------
    # Course
    # ---------------------------
    path("courses/", course_view.CourseListCreateView.as_view(), name="course-list"),
    path("courses/<uuid:pk>/", course_view.CourseDetailView.as_view(), name="course-detail"),
    path("courses/<uuid:course_id>/publish/", course_view.CoursePublishView.as_view(), name="course-publish"),
    path("courses/<uuid:course_id>/enroll/", course_view.CourseEnrollView.as_view(), name="course-enroll"),

    # ---------------------------
    # Module (nested under course)
    # ---------------------------
    path("courses/<uuid:course_id>/modules/", views.ModuleListCreateView.as_view(), name="module-list"),
    path("modules/<uuid:pk>/", views.ModuleDetailView.as_view(), name="module-detail"),
    path("courses/<uuid:course_id>/modules/reorder/", views.ModuleReorderView.as_view(), name="module-reorder"),

    # ---------------------------
    # Lesson (nested under module)
    # ---------------------------
    path("modules/<uuid:module_id>/lessons/", views.LessonListCreateView.as_view(), name="lesson-list"),
    path("lessons/<uuid:pk>/", views.LessonDetailView.as_view(), name="lesson-detail"),
    path("lessons/<uuid:lesson_id>/publish/", views.LessonPublishView.as_view(), name="lesson-publish"),

    # ---------------------------
    # Lesson Versions (nested under lesson)
    # ---------------------------
    path("lessons/<uuid:lesson_id>/versions/", views.LessonVersionListCreateView.as_view(), name="lessonversion-list"),
    path("lesson-versions/<uuid:pk>/", views.LessonVersionDetailView.as_view(), name="lessonversion-detail"),
    path("lessons/<uuid:lesson_id>/versions/publish/", views.LessonVersionPublishView.as_view(), name="lessonversion-publish"),

    # ---------------------------
    # Content Blocks (nested under lesson_version)
    # ---------------------------
    path("lesson-versions/<uuid:lesson_version_id>/blocks/", views.ContentBlockListCreateView.as_view(), name="contentblock-list"),
    path("content-blocks/<uuid:pk>/", views.ContentBlockDetailView.as_view(), name="contentblock-detail"),

    # ---------------------------
    # Explorations
    # ---------------------------
    path("explorations/", views.ExplorationListCreateView.as_view(), name="exploration-list"),
    path("explorations/<uuid:pk>/", views.ExplorationDetailView.as_view(), name="exploration-detail"),
    path("explorations/<uuid:exploration_id>/publish/", views.ExplorationPublishView.as_view(), name="exploration-publish"),

    # ---------------------------
    # Exploration States
    # ---------------------------
    path("explorations/<uuid:exploration_id>/states/", views.ExplorationStateListCreateView.as_view(), name="explorationstate-list"),
    path("exploration-states/<uuid:pk>/", views.ExplorationStateDetailView.as_view(), name="explorationstate-detail"),

    # ---------------------------
    # Exploration Transitions
    # ---------------------------
    path("explorations/<uuid:exploration_id>/transitions/", views.ExplorationTransitionListCreateView.as_view(), name="explorationtransition-list"),
    path("exploration-transitions/<uuid:pk>/", views.ExplorationTransitionDetailView.as_view(), name="explorationtransition-detail"),
]
