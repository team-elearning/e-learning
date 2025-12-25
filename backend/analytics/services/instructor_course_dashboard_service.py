from datetime import timedelta
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Avg, F, Q, OuterRef, Subquery, FloatField
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from typing import List, Union

from content.models import Course, Enrollment
from analytics.models import StudentSnapshot, CourseAnalyticsLog
from analytics.domains.course_health_overview_domain import CourseHealthOverviewDomain
from analytics.domains.student_risk_info_domain import StudentRiskInfoDomain
from analytics.domains.daily_metric_domain import DailyMetricDomain
from analytics.domains.risk_distribution_domain import RiskDistributionDomain
from analytics.domains.course_trend_domain import CourseTrendDomain
from analytics.domains.paginated_student_list_domain import PaginatedStudentListDomain



# ==========================================
# PUBLIC INTERFACE (HELPER)
# ==========================================

def _calculate_risk_distribution(queryset) -> RiskDistributionDomain:
    """Helper tính toán phân bố rủi ro từ QuerySet"""
    risk_counts = queryset.values('risk_level').annotate(total=Count('id'))
    count_map = {item['risk_level']: item['total'] for item in risk_counts}
    
    return RiskDistributionDomain(
        low=count_map.get('low', 0),
        medium=count_map.get('medium', 0),
        high=count_map.get('high', 0),
        critical=count_map.get('critical', 0)
    )


def _get_weekly_chart_data(course_id: str) -> List[DailyMetricDomain]:
    """
    Worker 2: Lấy dữ liệu Time Series cho biểu đồ (Last 7 Days).
    Sử dụng TruncDate để Group By theo ngày.
    """
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6) # Lấy cả hôm nay là 7 ngày

    # Query: Group by Ngày -> Avg Score của ngày đó
    # Lưu ý: Đây là trung bình cộng của TẤT CẢ snapshot trong ngày đó
    daily_stats = StudentSnapshot.objects.filter(
        course_id=course_id,
        created_at__date__gte=seven_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        avg_eng=Avg('engagement_score'),
        avg_perf=Avg('performance_score')
    ).order_by('date')

    # Convert QuerySet thành Dict để dễ tra cứu (xử lý ngày bị khuyết)
    data_map = {item['date']: item for item in daily_stats}

    # Tạo list đầy đủ 7 ngày (Fill 0 nếu ngày đó không có dữ liệu cronjob chạy)
    result_list = []
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        record = data_map.get(day)
        
        if record:
            result_list.append(DailyMetricDomain(
                date=day.strftime('%Y-%m-%d'),
                avg_engagement=round(record['avg_eng'] or 0, 1),
                avg_performance=round(record['avg_perf'] or 0, 1)
            ))
        else:
            # Nếu ngày đó server sập hoặc cronjob không chạy -> Điền 0 hoặc lấy giá trị ngày trước đó
            # Ở đây ta điền 0 để biểu đồ thể hiện sự đứt quãng
            result_list.append(DailyMetricDomain(
                date=day.strftime('%Y-%m-%d'),
                avg_engagement=0.0,
                avg_performance=0.0
            ))
            
    return result_list


def _calculate_trend_from_chart(chart_data: List[DailyMetricDomain], metric_name: str) -> str:
    """
    Worker 3: Tính xu hướng dựa trên dữ liệu biểu đồ.
    So sánh trung bình 3 ngày đầu vs 3 ngày cuối để mượt mà hơn.
    """
    if len(chart_data) < 2:
        return 'stable'
        
    # Lấy giá trị đầu và cuối (bỏ qua giá trị 0 nếu cronjob lỗi)
    valid_values = [
        getattr(d, metric_name) 
        for d in chart_data 
        if getattr(d, metric_name) > 0
    ]
    
    if not valid_values:
        return 'stable'
        
    start_val = valid_values[0]
    end_val = valid_values[-1]
    
    delta = end_val - start_val
    
    # Ngưỡng (Threshold): Thay đổi > 0.5 điểm trên thang 10 mới coi là xu hướng
    if delta > 0.5: return 'up'
    if delta < -0.5: return 'down'
    return 'stable'


def _generate_insight(risk_dist, total, trend_eng):
    """Sinh câu nhận xét thông minh"""
    if total == 0: return "Lớp học chưa có dữ liệu."
    
    danger_count = risk_dist.critical + risk_dist.high
    danger_percent = (danger_count / total) * 100
    
    msg = ""
    if danger_percent > 30:
        msg = f"⚠️ Cảnh báo: {int(danger_percent)}% lớp đang gặp nguy hiểm."
    elif danger_percent > 10:
        msg = f"⚠️ Có {danger_count} bạn cần hỗ trợ."
    else:
        msg = "✅ Lớp học đang duy trì phong độ tốt."
        
    if trend_eng == 'down':
        msg += " Mức độ chuyên cần đang giảm so với tuần trước."
    elif trend_eng == 'up':
        msg += " Tinh thần học tập đang đi lên!"
        
    return msg


def _empty_overview(course_id, course_title, course_published, status='pending', last_run=None):
    """Trả về domain rỗng"""
    return CourseHealthOverviewDomain(
        course_id=str(course_id),
        title=course_title,                   # [ADDED]
        status='active' if course_published else 'draft', # [ADDED]
        total_students=0,
        avg_engagement_score=0.0,
        avg_performance_score=0.0,
        avg_inactive_days=0,
        risk_distribution=RiskDistributionDomain(),
        last_updated_at=last_run,
        data_status=status
    )


# ==========================================
# PUBLIC INTERFACE (COURSE OVERVIEW)
# ==========================================

def get_course_health_overview(course_id: str) -> CourseHealthOverviewDomain:
    """
    Trả về các thẻ số liệu (Metrics Cards) và Pie Chart.
    Load cực nhanh (< 50ms).
    """
    course = get_object_or_404(Course.objects.only('title', 'published'), pk=course_id)

    # 1. Lấy thông tin lần chạy Job gần nhất (Bất kể thành công hay thất bại)
    latest_job = CourseAnalyticsLog.objects.filter(course_id=course_id).order_by('-created_at').first()
    
    # Nếu chưa chạy bao giờ
    if not latest_job:
        return _empty_overview(course_id, course.title, course.published, status="never_run")

    # Nếu job đang chạy hoặc vừa thất bại
    if latest_job.status == 'failed':
        return _empty_overview(course_id, course.title, course.published, status="failed", last_run=latest_job.created_at)

    # 1. Lấy tất cả snapshot mới nhất của khóa học
    # (Giả định Batch Job đã dọn dẹp các snapshot cũ trong ngày)
    snapshots_qs = StudentSnapshot.objects.filter(course_id=course_id)
    total_students = snapshots_qs.count()
    
    # Nếu chưa có dữ liệu nào
    if total_students == 0:
        return _empty_overview(course_id, course.title, course.published)

    # 2. Aggregation (Tính trung bình toàn lớp)
    # SQL: SELECT AVG(engagement_score), AVG(performance_score)...
    aggs = snapshots_qs.aggregate(
        avg_eng=Avg('engagement_score'),
        avg_perf=Avg('performance_score'),
        avg_inactive=Avg('days_inactive')
    )

    risk_dist = _calculate_risk_distribution(snapshots_qs)
    
    return CourseHealthOverviewDomain(
        course_id=str(course_id),
        title=course.title,                                  
        status='active' if course.published else 'draft',
        total_students=total_students,
        
        avg_engagement=round(aggs['avg_eng'] or 0, 1),
        avg_performance=round(aggs['avg_perf'] or 0, 1),
        avg_inactive_days=int(aggs['avg_inactive'] or 0),
        
        risk_distribution=risk_dist,
        
        last_updated_at=latest_job.created_at,
        data_status='up_to_date'
    )


def get_course_trends(course_id: str):
    """
    Trả về dữ liệu vẽ biểu đồ (Line Chart) và Insight text.
        Tách riêng ra để Frontend lazy load.
    """
    # Tạo Key định danh duy nhất
    cache_key = f"course_pulse_{course_id}"
        
    # Thử lấy từ Cache
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
        
    # 1. Lấy dữ liệu biểu đồ 7 ngày (Aggregation theo ngày)
    chart_data = _get_weekly_chart_data(course_id)

    # 2. Tính xu hướng dựa trên dữ liệu biểu đồ
    trend_eng = _calculate_trend_from_chart(chart_data, 'avg_engagement')
    trend_perf = _calculate_trend_from_chart(chart_data, 'avg_performance')

    # 3. Generate Insight (Cần risk_dist, ta tính lại nhanh hoặc truyền từ FE lên nếu muốn tối ưu cực đoan)
    # Ở đây tính lại cho decoupled, query count group by rất nhẹ.
    snapshots_qs = StudentSnapshot.objects.filter(course_id=course_id)
    risk_dist = _calculate_risk_distribution(snapshots_qs)

    # 4. Sinh Insight
    insight = _generate_insight(risk_dist, snapshots_qs.count(), trend_eng)
    
    result_domain = CourseTrendDomain(
        course_id=str(course_id),
        chart_data=chart_data,
        trend_engagement=trend_eng,
        trend_performance=trend_perf,
        insight_text=insight
    )

    # # Lưu vào Cache (1 tiếng - 3600s)
    # # Timeout này là "phòng hờ". Nếu ta quên xóa cache, nó cũng tự hết hạn sau 1h.
    # cache.set(cache_key, result_domain, timeout=3600)
    
    return result_domain


def get_student_risks_queryset(course_id: str):
    """
    Trả về QuerySet gốc đã được tối ưu hóa:
    1. Join với bảng User (select_related).
    2. Join ngầm với bảng Enrollment để lấy % (Subquery).
    """
    # A. Subquery lấy % hoàn thành (Chỉ lấy 1 giá trị)
    enrollment_subquery = Enrollment.objects.filter(
        user_id=OuterRef('user_id'),
        course_id=course_id
    ).values('percent_completed')[:1]

    # B. Main Query
    # Annotate giúp gắn thêm field 'real_percent_completed' vào mỗi object StudentSnapshot
    return StudentSnapshot.objects.filter(course_id=course_id)\
        .select_related('user')\
        .annotate(
            real_percent_completed=Subquery(enrollment_subquery, output_field=FloatField())
        ).order_by('engagement_score', '-days_inactive')


