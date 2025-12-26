import numpy as np
import pandas as pd
import time
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Avg, Max, F, Q
from django.utils import timezone
from datetime import timedelta
from typing import Optional, List, Union

# Import Models
from content.models import Enrollment, Course, Lesson, Quiz
from progress.models import QuizAttempt
from analytics.models import UserActivityLog, StudentSnapshot, CourseAnalyticsLog
from analytics.domains.analytics_result_domain import AnalyticsJobResultDomain
from analytics.domains.course_health_overview_domain import CourseHealthOverviewDomain
from analytics.domains.risk_distribution_domain import RiskDistributionDomain
from analytics.domains.paginated_student_list_domain import PaginatedStudentListDomain
from analytics.domains.student_risk_info_domain import StudentRiskInfoDomain
from analytics.domains.analytics_log_domain import AnalyticsLogDomain



# --- CONFIGURATION (Nên đưa vào Settings hoặc DB Config) ---
RISK_CONFIG = {
    'INACTIVE_WARN_DAYS': 7,
    'INACTIVE_CRITICAL_DAYS': 21,
    'LOW_ENGAGEMENT_THRESHOLD': 3.0,
    'LOW_PERFORMANCE_THRESHOLD': 5.0,
    'HIGH_PERFORMANCE_THRESHOLD': 8.0,
} 

# ---------------------------------------------------------
# PRIVATE HELPER METHODS 
# ---------------------------------------------------------

def _fetch_enrolled_students(course_id: str) -> pd.DataFrame:
    """Lấy danh sách học viên và % tiến độ"""
    enrollments = Enrollment.objects.filter(course_id=course_id).values('user_id', 'percent_completed')
    df = pd.DataFrame(list(enrollments))
    if not df.empty:
        df.set_index('user_id', inplace=True)
    return df


def _calculate_engagement_metrics(course_id: str, student_ids: list) -> pd.DataFrame:
    """Tính toán chỉ số tương tác từ UserActivityLog"""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Query Aggregate trực tiếp từ DB (Tối ưu RAM)
    log_stats_qs = UserActivityLog.objects.filter(
        course_id=course_id,
        timestamp__gte=thirty_days_ago,
        user_id__in=student_ids
    ).values('user_id').annotate(
        last_access=Max('timestamp'),
        total_actions=Count('id'),
        high_value_actions=Count('id', filter=Q(action__in=['QUIZ_SUBMIT', 'VIDEO_COMPLETE']))
    )

    if not log_stats_qs:
        # Trả về DataFrame rỗng nhưng có đúng cột để join không bị lỗi
        return pd.DataFrame(index=student_ids, columns=['days_inactive', 'eng_score']).fillna(0)

    df = pd.DataFrame(list(log_stats_qs))
    df.set_index('user_id', inplace=True)
    
    # Tính toán
    now = pd.Timestamp.now(tz='utc')
    if df['last_access'].dt.tz is None:
            df['last_access'] = df['last_access'].dt.tz_localize('UTC')
            
    df['days_inactive'] = (now - df['last_access']).dt.days
    
    # Công thức Engagement Score
    df['eng_score'] = (
        (df['total_actions'] + df['high_value_actions'] * 4) / 10
    ).clip(upper=10.0)
    
    return df[['days_inactive', 'eng_score']]


def _calculate_performance_metrics(course_id: str, student_ids: list) -> pd.DataFrame:
    """Tính toán điểm số trung bình từ QuizAttempt"""
    # Logic tính điểm normalized
    attempts = QuizAttempt.objects.filter(
        enrollment__course_id=course_id,
        status='graded',
        user_id__in=student_ids
    ).values('user_id', 'score', 'max_score')
    
    if not attempts:
        return pd.DataFrame(index=student_ids, columns=['avg_quiz_score']).fillna(0)

    df = pd.DataFrame(list(attempts))
    
    # Vectorized Normalization (Tránh chia cho 0)
    df['normalized'] = np.where(
        df['max_score'] > 0, 
        (df['score'] / df['max_score']) * 10, 
        0.0
    )
    
    # Group by user để lấy điểm trung bình
    quiz_avg = df.groupby('user_id')['normalized'].mean()
    return quiz_avg.to_frame(name='avg_quiz_score')


def _assess_risk_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Áp dụng logic phân loại rủi ro (Risk Matrix)"""
    # 1. Tính Performance Score tổng hợp
    df['perf_score'] = (
        (df['avg_quiz_score'] * 0.6) + 
        ((df['percent_completed'] / 10) * 0.4)
    ).round(2)

    # 2. Phạt điểm Engagement nếu nghỉ quá lâu
    df['eng_score'] = np.where(
        df['days_inactive'] > RISK_CONFIG['INACTIVE_WARN_DAYS'], 
        df['eng_score'] * 0.5, 
        df['eng_score']
    )
    # Nếu nghỉ quá 2 tuần -> Engagement về 0
    df['eng_score'] = np.where(df['days_inactive'] > 14, 0.0, df['eng_score'])

    # 3. Phân loại (Logic if/else ma trận)
    c_dropout = df['days_inactive'] > RISK_CONFIG['INACTIVE_CRITICAL_DAYS']
    c_at_risk = (df['days_inactive'] > RISK_CONFIG['INACTIVE_WARN_DAYS']) | (df['eng_score'] < RISK_CONFIG['LOW_ENGAGEMENT_THRESHOLD'])
    c_struggling = (df['eng_score'] >= 6.0) & (df['perf_score'] < RISK_CONFIG['LOW_PERFORMANCE_THRESHOLD'])
    c_disengaged = (df['perf_score'] >= RISK_CONFIG['HIGH_PERFORMANCE_THRESHOLD']) & (df['eng_score'] < 5.0)

    df['risk_level'] = np.select(
        [c_dropout, c_at_risk, c_struggling, c_disengaged], 
        ['critical', 'high', 'medium', 'medium'], 
        default='low'
    )

    df['message'] = np.select(
        [c_dropout, c_at_risk, c_struggling, c_disengaged], 
        [
            f"Vắng mặt > {RISK_CONFIG['INACTIVE_CRITICAL_DAYS']} ngày", 
            'Tương tác thấp (Cần nhắc nhở)', 
            'Điểm thấp dù chăm chỉ (Cần hỗ trợ)', 
            'Học đối phó/Giỏi nhưng lười'
        ], 
        default='Kết quả tốt'
    )
    return df


# ==========================================
# ANALYZE
# ==========================================

@transaction.atomic
def analyze_course_health_bulk(course_id: str) -> AnalyticsJobResultDomain:
    start_time = time.time()
    
    # 1. Fetch Students (Base Population)
    df_students = _fetch_enrolled_students(course_id)
    if df_students.empty:
        return AnalyticsJobResultDomain(course_id, 0, 0, 'skipped_empty', 0)
    
    student_ids = df_students.index.tolist()

    # 2. Calculate Engagement (Từ Log)
    df_engagement = _calculate_engagement_metrics(course_id, student_ids)
    
    # 3. Calculate Performance (Từ Quiz)
    df_performance = _calculate_performance_metrics(course_id, student_ids)
    
    # 4. Merge & Final Risk Assessment
    # Join các dataframe lại với nhau
    df_final = df_students.join(df_engagement, how='left')\
                            .join(df_performance, how='left')
    
    # Điền 0 cho những user không có log/quiz
    df_final.fillna(0, inplace=True)
    
    # Chạy logic phân loại rủi ro
    df_result = _assess_risk_matrix(df_final)

    # 5. Save to DB
    save_snapshots(course_id, df_result)

    execution_time = round(time.time() - start_time, 2)
    return AnalyticsJobResultDomain(
        course_id=str(course_id),
        total_students=len(df_students),
        processed_count=len(df_result),
        status='success',
        execution_time=execution_time
    )


# ==========================================
# SNAPSHOT
# ==========================================

@transaction.atomic
def save_snapshots(course_id, df_result):
    """
    Lưu kết quả phân tích.
    LOGIC MỚI: Giữ lại lịch sử (Append-only), không xóa cái cũ.
    Để tránh spam DB, ta có thể check xem hôm nay đã chạy chưa (Optional).
    """
    
    # [OPTIONAL]: Xóa bản ghi CỦA NGÀY HÔM NAY để tránh duplicate nếu chạy job nhiều lần trong ngày
    # Giữ lại bản ghi của ngày hôm qua, tuần trước...
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    deleted_count, _ = StudentSnapshot.objects.filter(
        course_id=course_id, 
        created_at__gte=today_start # Chỉ xóa cái vừa tạo hôm nay (nếu chạy lại)
    ).delete()
    
    if deleted_count > 0:
        print(f"🔄 Re-running analytics for today. Deleted {deleted_count} partial records.")

    # Chuẩn bị list object
    snapshots = []
    for user_id, row in df_result.iterrows():
        snapshots.append(StudentSnapshot(
            user_id=user_id,
            course_id=course_id,
            
            # Các chỉ số
            engagement_score=row['eng_score'],
            performance_score=row['perf_score'],
            days_inactive=int(row['days_inactive']),
            
            # Kết luận
            risk_level=row['risk_level'],
            ai_message=row['message'],
            
            # [QUAN TRỌNG] Lưu ý: created_at sẽ tự động lấy giờ hiện tại (auto_now_add)
        ))
    
    # Bulk Create (Insert 1 cục)
    StudentSnapshot.objects.bulk_create(snapshots, batch_size=500)
    print(f"✅ Saved history for {len(snapshots)} students in Course {course_id}")

    # ---------------------------------------------------------
    # 3. [NEW] UPDATE ENROLLMENT (SYNC STATE) - Dùng bulk_update
    # ---------------------------------------------------------
    print("⏳ Syncing to Enrollment table...")

    # Bước A: Lấy tất cả enrollment cần update lên RAM (1 Query)
    # df_result.index chính là list các user_id vừa được tính toán
    enrollments_to_update = Enrollment.objects.filter(
        course_id=course_id,
        user_id__in=df_result.index
    )

    # Bước B: Map dữ liệu từ DataFrame vào Object (In-Memory)
    update_list = []
    
    for enrollment in enrollments_to_update:
        # Lấy row tương ứng từ DataFrame (O(1) lookup vì dùng index)
        try:
            row = df_result.loc[enrollment.user_id]
            
            # Gán giá trị mới vào object Enrollment
            enrollment.current_engagement_score = float(row['eng_score'])
            enrollment.current_performance_score = float(row['perf_score'])
            enrollment.current_days_inactive = int(row['days_inactive'])
            enrollment.current_risk_level = row['risk_level']
            
            update_list.append(enrollment)
        except KeyError:
            # Phòng trường hợp data bị lệch (hiếm khi xảy ra nếu logic chuẩn)
            continue

    # Bước C: Bắn 1 query UPDATE xuống DB
    if update_list:
        Enrollment.objects.bulk_update(
            update_list,
            fields=[
                'current_engagement_score', 
                'current_performance_score', 
                'current_days_inactive', 
                'current_risk_level'
            ],
            batch_size=500
        )
        print(f"✅ Synced current state for {len(update_list)} enrollments.")
    
    instructor_id = Course.objects.filter(id=course_id).values_list('owner_id', flat=True).first()

    if instructor_id:
        cache_key = f"course_pulse_{course_id}"
        cache_overview = f"instructor_overview_{instructor_id}" 
        
        cache.delete_many([cache_key, cache_overview])
        print(f"♻️ Cache invalidated for Course {course_id} & Instructor {instructor_id}")
    else:
        print("⚠️ Warning: Could not find instructor to clear cache.")


