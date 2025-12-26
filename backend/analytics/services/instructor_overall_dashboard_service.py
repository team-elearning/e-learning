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
from analytics.domains.course_health_overview_domain import CourseHealthOverviewDomain
from analytics.domains.risk_distribution_domain import RiskDistributionDomain



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


def _calculate_global_health(instructor_id):
    """
    Tối ưu hóa việc lấy trạng thái mới nhất.
    Cách tốt nhất: Dùng bảng Enrollment (trạng thái hiện tại).
    Cách thay thế (nếu phải dùng Snapshot):
    """
    # Cách query nhanh nhất để lấy state cuối cùng của mỗi user trong mỗi course
    # Yêu cầu: Enrollment nên được update mỗi khi có Snapshot mới
    
    agg = Enrollment.objects.filter(
        course__owner_id=instructor_id,
        course__published=True
    ).aggregate(
        avg_eng=Avg('current_engagement_score'), # Giả sử Enrollment có field này
        avg_perf=Avg('current_performance_score'),
        critical_count=Count('id', filter=Q(current_risk_level__in=['high', 'critical']))
    )

    # Nếu Enrollment chưa có field cached, bắt buộc query Snapshot (Sẽ chậm)
    # Code cũ của bạn dùng distinct('user', 'course') chỉ chạy trên Postgres và khá nặng.
    
    return {
        'avg_eng': round(agg['avg_eng'] or 0, 1),
        'avg_perf': round(agg['avg_perf'] or 0, 1),
        'critical_count': agg['critical_count'] or 0
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
    ranking_qs = Enrollment.objects.filter(
        course__owner_id=instructor_id
    ).values(
        'course_id', 'course__title', 'course__published'
    ).annotate(
        student_count=Count('id'),

        avg_eng=Avg('current_engagement_score'), # Lấy từ field mới thêm
        avg_perf=Avg('current_performance_score'),
        avg_inactive=Avg('current_days_inactive'),

        cnt_low=Count('id', filter=Q(current_risk_level='low')),
        cnt_medium=Count('id', filter=Q(current_risk_level='medium')),
        cnt_high=Count('id', filter=Q(current_risk_level='high')),
        cnt_critical=Count('id', filter=Q(current_risk_level='critical')),
    ).order_by('-avg_eng') # Mặc định sort điểm cao xuống thấp

    # Convert to DTO List
    summary_list = []
    for item in ranking_qs:
        risk_dist = RiskDistributionDomain(
            low=item['cnt_low'],
            medium=item['cnt_medium'],
            high=item['cnt_high'],
            critical=item['cnt_critical']
        )

        course_health = CourseHealthOverviewDomain(
            course_id=str(item['course_id']),
            title=item['course__title'],
            status='active' if item['course__published'] else 'draft',
            total_students=item['student_count'],

            avg_engagement=round(item['avg_eng'] or 0, 1),
            avg_performance=round(item['avg_perf'] or 0, 1),
            avg_inactive_days=int(item['avg_inactive'] or 0),

            # -> Đã có full distribution để Frontend vẽ Mini Stacked Bar
            risk_distribution=risk_dist,
            
            data_status='up_to_date'
        )
        summary_list.append(course_health)

    # Top 3 khóa tốt nhất
    top_courses = summary_list[:3]
    
    # Các khóa cần chú ý: Là các khóa có avg_eng thấp (dưới 5.0) HOẶC có nhiều risk_count
    # Sắp xếp lại list theo risk_count giảm dần để lấy những khóa báo động
    attention_list = sorted(
        summary_list, 
        key=lambda x: x.risk_distribution.high + x.risk_distribution.critical, 
        reverse=True)
    
    courses_needing_attention = [
        c for c in attention_list 
        if (c.risk_distribution.high + c.risk_distribution.critical) > 0
    ][:3]

    return top_courses, courses_needing_attention


# ==========================================
# OVERVIEW
# ==========================================

def get_instructor_overview(instructor_id: str) -> InstructorOverviewDomain:
    # cache_key = f"instructor_overview_{instructor_id}"
    # cached_data = cache.get(cache_key)

    # if cached_data:
    #     return cached_data
    
    stats  = _calculate_headline_stats(instructor_id)
    
    total_revenue = stats['revenue']
    unique_students = stats['students']
    total_enrollments = stats['enrollments']

    active_courses_count = Course.objects.filter(
        owner_id=instructor_id, published=True
    ).count()

    # 3. Global Health (TỐI ƯU: Query thẳng từ Enrollment thay vì Snapshot nếu có trường score ở đó)
    # Giả sử Enrollment model đã có field: current_engagement_score, current_risk_level
    # Nếu bắt buộc dùng Snapshot, hãy dùng Subquery để tối ưu thay vì sort python
    health_stats = _calculate_global_health(instructor_id)

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