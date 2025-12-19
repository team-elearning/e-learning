from django.core.cache import cache
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from typing import List

from content.models import Course, Enrollment
from analytics.models import StudentSnapshot
from analytics.domains.instructor_overview_domain import InstructorOverviewDomain
from analytics.domains.daily_metric_domain import DailyMetricDomain
from analytics.domains.course_summary_domain import CourseSummaryDomain



# ==========================================
# PRIVATE HELPERS
# ==========================================

def _calculate_headline_stats(instructor_id):
    """Tách nhỏ logic tính tiền nong"""
    # 1. HEADLINE STATS (Tài chính & Quy mô)
    # Query bảng Enrollment, join sang Course để check owner
    stats = Enrollment.objects.filter(
        course__owner_id=instructor_id
    ).aggregate(
        total_enrollments=Count('id'),
        total_revenue=Sum('course__price'), # Tính tổng doanh thu (nếu có logic phức tạp hơn thì cần service riêng)
        # count(distinct user) để biết số học viên thực tế (1 người học 2 khóa chỉ tính 1)
        unique_students=Count('user', distinct=True) 
    )
    
    # Xử lý None -> 0 ngay tại đây
    return {
        'revenue': int(stats['total_revenue'] or 0),
        'students': stats['unique_students'] or 0,
        'enrollments': stats['total_enrollments'] or 0
    }


def _get_global_chart_data(instructor_id) -> List[DailyMetricDomain]:
    """
    Lấy biểu đồ Engagement trung bình của TOÀN BỘ khóa học do giảng viên này dạy.
    Giúp trả lời: "Tuần qua chất lượng dạy học chung của tôi thế nào?"
    """
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6)

    # Group by Date -> Avg Engagement
    daily_stats = StudentSnapshot.objects.filter(
        course__owner_id=instructor_id,
        created_at__date__gte=seven_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        avg_eng=Avg('engagement_score'),
        avg_perf=Avg('performance_score')
    ).order_by('date')

    data_map = {item['date']: item for item in daily_stats}
    result_list = []
    
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        record = data_map.get(day)
        
        # Nếu ngày đó ko có data (không chạy job), điền 0 hoặc logic fallback
        avg_eng = round(record['avg_eng'], 1) if record else 0.0
        avg_perf = round(record['avg_perf'], 1) if record else 0.0

        result_list.append(DailyMetricDomain(
            date=day.strftime('%Y-%m-%d'),
            avg_engagement=avg_eng,
            avg_performance=avg_perf
        ))
        
    return result_list


def _get_course_rankings(instructor_id):
    """
    Tìm ra các khóa học Tốt Nhất và các khóa học Cần Chú Ý.
    Dựa trên Engagement Score trung bình của từng khóa.
    """
    # Aggregate theo từng khóa học
    # course__title lấy từ quan hệ ForeignKey trong StudentSnapshot
    ranking_qs = StudentSnapshot.objects.filter(
        course__owner_id=instructor_id
    ).values(
        'course_id', 'course__title', 'course__published'
    ).annotate(
        avg_eng=Avg('engagement_score'),
        risk_count=Count('id', filter=Q(risk_level__in=['high', 'critical'])),
        student_count=Count('user', distinct=True)
    ).order_by('-avg_eng') # Mặc định sort điểm cao xuống thấp

    # Convert to DTO List
    summary_list = []
    for item in ranking_qs:
        summary_list.append(CourseSummaryDomain(
            course_id=str(item['course_id']),
            title=item['course__title'],
            total_students=item['student_count'],
            avg_engagement=round(item['avg_eng'] or 0, 1),
            risk_count=item['risk_count'],
            status='active' if item['course__published'] else 'draft'
        ))

    # Top 3 khóa tốt nhất
    top_courses = summary_list[:3]
    
    # Các khóa cần chú ý: Là các khóa có avg_eng thấp (dưới 5.0) HOẶC có nhiều risk_count
    # Sắp xếp lại list theo risk_count giảm dần để lấy những khóa báo động
    attention_list = sorted(summary_list, key=lambda x: x.risk_count, reverse=True)
    courses_needing_attention = [c for c in attention_list if c.risk_count > 0][:3]

    return top_courses, courses_needing_attention


# ==========================================
# OVERVIEW
# ==========================================

def get_instructor_overview(instructor_id: str) -> InstructorOverviewDomain:
    cache_key = f"instructor_overview_{instructor_id}"
    cached_data = cache.get(cache_key)

    if cached_data:
        return cached_data
    
    stats  = _calculate_headline_stats(instructor_id)\
    
    total_revenue = stats['revenue']
    unique_students = stats['students']
    total_enrollments = stats['enrollments']

    active_courses_count = Course.objects.filter(
        owner_id=instructor_id, published=True
    ).count()

    # 2. GLOBAL HEALTH (Sức khỏe chung)
    # Lấy snapshot mới nhất của TẤT CẢ học viên thuộc TẤT CẢ khóa của giảng viên này
    # Filter: course__owner_id
    latest_snapshots = StudentSnapshot.objects.filter(
        course__owner_id=instructor_id
    ).order_by('user', 'course', '-created_at').distinct('user', 'course')

    health_stats = latest_snapshots.aggregate(
        avg_eng=Avg('engagement_score'),
        avg_perf=Avg('performance_score'),
        # Đếm số snapshot có mức rủi ro cao
        critical_count=Count('id', filter=Q(risk_level__in=['high', 'critical']))
    )

    # 3. GLOBAL CHART (Biểu đồ diễn biến 7 ngày qua)
    chart_data = _get_global_chart_data(instructor_id)

    # 4. RANKING (Xếp hạng khóa học)
    top_courses, attention_courses = _get_course_rankings(instructor_id)

    result = InstructorOverviewDomain(
        instructor_id=str(instructor_id),
        
        total_revenue=total_revenue,
        total_students=unique_students,
        total_enrollments=total_enrollments,
        active_courses_count=active_courses_count,
        
        global_engagement=round(health_stats['avg_eng'] or 0, 1),
        global_performance=round(health_stats['avg_perf'] or 0, 1),
        critical_students_total=health_stats['critical_count'] or 0,
        
        chart_data=chart_data,
        
        top_performing_courses=top_courses,
        courses_needing_attention=attention_courses
    )

    # # Lưu vào cache 6 tiếng 
    # # Khi có enrollment mới, ta có thể xóa cache này để user thấy update ngay
    # cache.set(cache_key, result, timeout=21600) 
    
    return result