from django.urls import path

from analytics.api.views.log_view import AnalyticsBatchView
from analytics.api.views.analytics_view import CourseHealthAnalyzeView
from analytics.api.views.instructor_dashboard_view import CourseHealthOverviewView, CourseAnalyticsTrendsView, InstructorOverviewView



urlpatterns = [
    path('batch/', AnalyticsBatchView.as_view(), name='analytics-activites-log'),
    
    path('instructor/overview/', InstructorOverviewView.as_view(), name='instructor-courses-overview'),

    # Instructor dashboard
    path('instructor/courses/<course_id>/analyze/', CourseHealthAnalyzeView.as_view(), name='instructor-course-analyze'),
    path('instructor/courses/<uuid:course_id>/overview/', CourseHealthOverviewView.as_view(), name='instructor-course-overview'),
    path('instructor/courses/<uuid:course_id>/trends/', CourseAnalyticsTrendsView.as_view(), name='instructor-course-trends'),
]