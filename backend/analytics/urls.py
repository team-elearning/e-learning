from django.urls import path

from analytics.api.views.log_view import AnalyticsBatchView
from analytics.api.views.instructor_dashboard_view import InstructorCourseHealthOverviewView, InstructorCourseAnalyticsTrendsView, InstructorOverviewView, InstructorCourseHealthAnalyzeView, InstructorCourseStudentsRiskListView



urlpatterns = [
    path('batch/', AnalyticsBatchView.as_view(), name='analytics-activites-log'),
    
    path('instructor/overview/', InstructorOverviewView.as_view(), name='instructor-courses-overview'),

    # Instructor dashboard
    path('instructor/courses/<uuid:course_id>/analyze/', InstructorCourseHealthAnalyzeView.as_view(), name='instructor-course-analyze'),
    path('instructor/courses/<uuid:course_id>/overview/', InstructorCourseHealthOverviewView.as_view(), name='instructor-course-overview'),
    path('instructor/courses/<uuid:course_id>/trends/', InstructorCourseAnalyticsTrendsView.as_view(), name='instructor-course-trends'),
    path('instructor/courses/<uuid:course_id>/students-risk-list/', InstructorCourseStudentsRiskListView.as_view(), name='instructor-course-students-risk-list'),
]