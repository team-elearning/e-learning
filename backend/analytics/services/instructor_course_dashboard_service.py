from datetime import timedelta
from django.core.cache import cache
from django.db.models import Count, Avg, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from typing import List

from content.models import Course
from analytics.models import StudentSnapshot
from analytics.domains.course_pulse_domain import CoursePulseDomain
from analytics.domains.student_risk_info_domain import StudentRiskInfoDomain
from analytics.domains.daily_metric_domain import DailyMetricDomain



# ==========================================
# PUBLIC INTERFACE (HELPER)
# ==========================================

def _get_current_status(course_id: str):
    """
    Worker 1: Tính toán trạng thái hiện tại (Real-time Snapshot).
    Sử dụng DISTINCT ON để lấy bản ghi mới nhất của mỗi học viên.
    """
    snapshots = StudentSnapshot.objects.filter(course_id=course_id)\
        .order_by('user', '-created_at')\
        .distinct('user')

    # Aggregate chỉ số trung bình
    stats = snapshots.aggregate(
        avg_eng=Avg('engagement_score'),
        avg_perf=Avg('performance_score'),
        avg_inactive=Avg('days_inactive')
    )

    # Tính phân phối rủi ro (Python loop nhanh hơn SQL phức tạp ở quy mô nhỏ)
    risk_dist = {'safe': 0, 'warning': 0, 'danger': 0}
    count = 0
    
    for snap in snapshots:
        count += 1
        if snap.risk_level == 'low':
            risk_dist['safe'] += 1
        elif snap.risk_level == 'medium':
            risk_dist['warning'] += 1
        else:
            risk_dist['danger'] += 1
            
    return stats, risk_dist, count


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


def _generate_insight(self, risk_dist, total, trend_eng):
    """Sinh câu nhận xét thông minh"""
    if total == 0: return "Lớp học chưa có dữ liệu."
    
    danger_percent = (risk_dist['danger'] / total) * 100
    
    msg = ""
    if danger_percent > 30:
        msg = f"⚠️ Cảnh báo: {int(danger_percent)}% lớp đang gặp nguy hiểm."
    elif danger_percent > 10:
        msg = f"⚠️ Có {risk_dist['danger']} bạn cần hỗ trợ."
    else:
        msg = "✅ Lớp học đang duy trì phong độ tốt."
        
    if trend_eng == 'down':
        msg += " Mức độ chuyên cần đang giảm so với tuần trước."
    elif trend_eng == 'up':
        msg += " Tinh thần học tập đang đi lên!"
        
    return msg


def _empty_pulse(course_id):
    """Trả về domain rỗng"""
    return CoursePulseDomain(
        course_id=str(course_id),
        status="pending",
        total_students=0,
        risk_distribution={'safe': 0, 'warning': 0, 'danger': 0},
        avg_engagement=0.0, avg_performance=0.0, avg_inactive_days=0,
        chart_data=[],
        trend_engagement='stable', trend_performance='stable',
        insight_text="Hệ thống đang thu thập dữ liệu (cần ít nhất 24h)."
    )


# ==========================================
# PUBLIC INTERFACE (COURSE OVERVIEW)
# ==========================================

def get_course_pulse(course_id: str):
    """
    Lấy 'Nhịp đập' của khóa học (Overview).
    Phù hợp để vẽ Pie Chart hoặc Bar Chart.
    Orchestrator: Điều phối các hàm con để lắp ráp thành Domain hoàn chỉnh.
    """
    # Tạo Key định danh duy nhất
    cache_key = f"course_pulse_{course_id}"
        
    # Thử lấy từ Cache
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # 1. Lấy trạng thái hiện tại (Snapshot mới nhất của từng user)
    current_stats, risk_dist, total_students = _get_current_status(course_id)

    # Nếu chưa có dữ liệu analytics nào
    if total_students == 0:
        return _empty_pulse(course_id)
    
    # 2. Lấy dữ liệu biểu đồ 7 ngày (Aggregation theo ngày)
    chart_data = _get_weekly_chart_data(course_id)

    # 3. Tính xu hướng dựa trên dữ liệu biểu đồ
    trend_eng = _calculate_trend_from_chart(chart_data, 'avg_engagement')
    trend_perf = _calculate_trend_from_chart(chart_data, 'avg_performance')

    # 4. Sinh Insight
    insight = _generate_insight(risk_dist, total_students, trend_eng)
    
    result_domain = CoursePulseDomain(
        course_id=str(course_id),
        status="ready",
        total_students=total_students,

        # Current Data
        risk_distribution=risk_dist,
        avg_engagement=round(current_stats['avg_eng'] or 0, 1),
        avg_performance=round(current_stats['avg_perf'] or 0, 1),
        avg_inactive_days=int(current_stats['avg_inactive'] or 0),
        
        # Chart Data
        chart_data=chart_data,

        trend_engagement=trend_eng,
        trend_performance=trend_perf,
        
        insight_text=insight
    )

    # # Lưu vào Cache (1 tiếng - 3600s)
    # # Timeout này là "phòng hờ". Nếu ta quên xóa cache, nó cũng tự hết hạn sau 1h.
    # cache.set(cache_key, result_domain, timeout=3600)
    
    return result_domain


def get_at_risk_students(course_id: str, limit=10) -> List[StudentRiskInfoDomain]:
    """
    Lấy danh sách 'Báo động đỏ' (High & Critical).
    """
    # Chỉ lấy những snapshot mới nhất mà có rủi ro cao
    queryset = StudentSnapshot.objects.filter(
        course_id=course_id,
        risk_level__in=['high', 'critical']
    ).select_related('user', 'user__profile')\
    .order_by('user', '-created_at').distinct('user')
    
    # Sắp xếp ưu tiên: Critical trước -> High sau -> Days inactive giảm dần
    # Vì distinct('user') yêu cầu order_by('user') đầu tiên, nên ta phải xử lý list bằng Python
    # hoặc dùng Subquery phức tạp. Ở đây xử lý Python cho gọn code (với limit nhỏ).
    
    candidates = list(queryset)
    
    # Sort thủ công: Critical lên đầu, sau đó đến số ngày nghỉ
    candidates.sort(key=lambda x: (x.risk_level == 'critical', x.days_inactive), reverse=True)
    
    results = []
    for snap in candidates:
        profile = getattr(snap.user, 'profile', None)
        name = profile.display_name if profile else snap.user.email
        avatar = profile.avatar_id if profile else None

        results.append(StudentRiskInfoDomain(
            user_id=str(snap.user.id),
            course_id=str(snap.course_id),
            engagement_score=snap.engagement_score,
            performance_score=snap.performance_score,
            days_inactive=snap.days_inactive,
            risk_level=snap.risk_level,
            reason=snap.ai_message,
            suggested_action=snap.suggested_action,
            
            # UI Fields
            student_name=name,
            student_avatar=avatar,
            last_updated=snap.created_at
        ))
        
    return results


