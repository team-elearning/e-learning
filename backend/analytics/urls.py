from django.urls import path

from analytics.api.views.log_view import AnalyticsBatchView
from analytics.api.views.analytics_view import CourseHealthAnalyzeView
from analytics.api.views.instructor_dashboard_view import CourseHealthOverviewView, CourseAnalyticsTrendsView



urlpatterns = [
    path('batch/', AnalyticsBatchView.as_view(), name='analytics-activites-log'),
    
    # Instructor dashboard
    path('instructor/courses/<course_id>/analytics/analyze/', CourseHealthAnalyzeView.as_view(), name='instructor-course-analyze'),
    path('instructor/courses/<uuid:course_id>/analytics/overview/', CourseHealthOverviewView.as_view(), name='instructor-analytics-overview'),
    path('instructor/courses/<uuid:course_id>/analytics/trends/', CourseAnalyticsTrendsView.as_view(), name='instructor-analytics-trends'),
]