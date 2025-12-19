import pandas as pd
import numpy as np
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Avg, Max, F, Q
from django.utils import timezone
from datetime import timedelta
from typing import Optional

# Import Models
from content.models import Enrollment, Course, Lesson, Quiz
from progress.models import QuizAttempt
from analytics.models import UserActivityLog, StudentSnapshot
from analytics.domains.student_profile_domain import StudentRiskProfile



# ==========================================
# ANALYZE
# ==========================================

def analyze_course_health_bulk(course_id: str):
    """
    Phân tích rủi ro cho toàn bộ học viên trong khóa học.
    Nên chạy qua Celery/Cronjob (ví dụ: mỗi đêm hoặc mỗi 6 tiếng).
    """
    # 1. PREPARE DATA (Lấy ID tham chiếu)
    # ---------------------------------------------------------
    # Lấy danh sách Lesson ID và Quiz ID thuộc khóa học để filter log
    lesson_ids = list(Lesson.objects.filter(module__course_id=course_id).values_list('id', flat=True))
    
    # Lấy Quiz ID thông qua ContentBlock (như bạn mô tả: ContentBlock -> Lesson -> Module -> Course)
    quiz_ids = list(Quiz.objects.filter(
        content_blocks__lesson__module__course_id=course_id
    ).values_list('id', flat=True))
    
    lesson_ids_str = [str(uid) for uid in lesson_ids]
    quiz_ids_str = [str(uid) for uid in quiz_ids]
    course_id_str = str(course_id)

    # 2. FETCH DATA (Chỉ 3 Queries lớn thay vì N+1)
    # ---------------------------------------------------------
    
    # Q1: Lấy danh sách học viên (Base DataFrame)
    # Chỉ lấy fields cần thiết để tiết kiệm RAM
    enrollments = Enrollment.objects.filter(course_id=course_id).values(
        'user_id', 'percent_completed'
    )
    if not enrollments: return # Khóa học vắng tanh
    
    df_students = pd.DataFrame(list(enrollments))
    df_students.set_index('user_id', inplace=True) # Index là User ID

    # Q2: Lấy Logs tương tác (30 ngày qua)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    logs = UserActivityLog.objects.filter(
        timestamp__gte=thirty_days_ago,
        # Filter Log thuộc về Course/Lesson/Quiz của khóa này
    ).filter(
        Q(entity_type='course', entity_id=course_id_str) |
        Q(entity_type='lesson', entity_id__in=lesson_ids_str) |
        Q(entity_type='quiz', entity_id__in=quiz_ids_str)
    ).values('user_id', 'action', 'timestamp')

    df_logs = pd.DataFrame(list(logs))
    
    # Q3: Lấy điểm Quiz (Lấy điểm trung bình của các bài đã chấm)
    # Filter theo quiz_ids thuộc khóa học
    attempts = QuizAttempt.objects.filter(
        quiz_id__in=quiz_ids,
        status='graded'
    ).values('user_id', 'score', 'max_score')
    
    df_quizzes = pd.DataFrame(list(attempts))

    # 3. MATRIX CALCULATION (Pandas Magic)
    # ---------------------------------------------------------

    # A. TÍNH ENGAGEMENT (Từ df_logs)
    if not df_logs.empty:
        # Convert timestamp
        df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
        now = pd.Timestamp.now(tz='utc') # Lưu ý timezone

        # Group by User để tính các chỉ số
        log_stats = df_logs.groupby('user_id').agg(
            last_access=('timestamp', 'max'),
            total_actions=('action', 'count'),
            # Đếm số action quan trọng (Lambda function hơi chậm, nhưng ok với data vừa phải)
            # Cách nhanh hơn: Tạo cột 'is_high_value' trước rồi sum
            high_value_actions=('action', lambda x: x.isin(['QUIZ_SUBMIT', 'VIDEO_COMPLETE']).sum())
        )

        # Tính days_inactive
        log_stats['days_inactive'] = (now - log_stats['last_access']).dt.days

        # Tính Engagement Score (Vector hóa công thức)
        # Score = (Total + HighVal * 4) / 10
        log_stats['eng_score_raw'] = (log_stats['total_actions'] + log_stats['high_value_actions'] * 4) / 10
        
        # Clip score về 10
        log_stats['eng_score'] = log_stats['eng_score_raw'].clip(upper=10.0)
        
        # Phạt điểm nếu inactive (Vector hóa logic if/else)
        # np.where(condition, true_val, false_val)
        log_stats['eng_score'] = np.where(log_stats['days_inactive'] > 7, log_stats['eng_score'] * 0.5, log_stats['eng_score'])
        log_stats['eng_score'] = np.where(log_stats['days_inactive'] > 14, 0.0, log_stats['eng_score'])
        
        # Merge vào bảng học sinh (Left Join - User nào ko có log thì NaN)
        df_final = df_students.join(log_stats, how='left')
    else:
        # Trường hợp không có log nào
        df_final = df_students.copy()
        df_final['eng_score'] = 0.0
        df_final['days_inactive'] = 30 # Default

    # B. TÍNH PERFORMANCE (Từ df_quizzes & df_students)
    if not df_quizzes.empty:
        # Chuẩn hóa điểm quiz về thang 10 (score / max_score * 10)
        df_quizzes['normalized_score'] = (df_quizzes['score'] / df_quizzes['max_score']) * 10
        # Tính trung bình điểm quiz mỗi user
        quiz_avg = df_quizzes.groupby('user_id')['normalized_score'].mean()
        
        df_final = df_final.join(quiz_avg.rename('avg_quiz_score'), how='left')
    else:
        df_final['avg_quiz_score'] = 0.0

    # Fill NaN bằng 0 (cho user không làm quiz hoặc ko có log)
    df_final.fillna(0, inplace=True)
    
    # Tính Performance Score tổng hợp
    # Perf = (AvgQuiz * 0.6) + ((PercentCompleted / 10) * 0.4)
    df_final['perf_score'] = (df_final['avg_quiz_score'] * 0.6) + ((df_final['percent_completed'] / 10) * 0.4)
    df_final['perf_score'] = df_final['perf_score'].round(2)
    
    # 4. RISK ASSESSMENT (Vectorized Logic)
    # ---------------------------------------------------------
    
    # Tạo cột Risk Level mặc định
    df_final['risk_level'] = 'low'
    df_final['message'] = 'Duy trì tốt'

    # Apply logic phân loại (Dùng np.select giống như SQL Case When)
    # Điều kiện
    cond_dropout = df_final['days_inactive'] > 21
    cond_at_risk = (df_final['days_inactive'] > 7) | (df_final['eng_score'] < 3.0)
    cond_struggling = (df_final['eng_score'] >= 6.0) & (df_final['perf_score'] < 5.0)
    cond_disengaged = (df_final['perf_score'] >= 8.0) & (df_final['eng_score'] < 5.0)

    # Giá trị tương ứng
    choices_risk = ['critical', 'high', 'medium', 'medium']
    choices_msg = [
        'Vắng mặt quá lâu (Dropout?)',
        'Ít tương tác (At Risk)',
        'Gặp khó khăn kiến thức (Struggling)',
        'Học tài tử (Disengaged)'
    ]

    # Áp dụng
    df_final['risk_level'] = np.select(
        [cond_dropout, cond_at_risk, cond_struggling, cond_disengaged], 
        choices_risk, 
        default='low'
    )
    df_final['message'] = np.select(
        [cond_dropout, cond_at_risk, cond_struggling, cond_disengaged], 
        choices_msg, 
        default='Kết quả tốt'
    )

    # 5. BULK SAVE TO DB
    # ---------------------------------------------------------
    save_snapshots(course_id, df_final)


# ==========================================
# SNAPSHOT
# ==========================================

@transaction.atomic
def save_snapshots(self, course_id, df_result):
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

    # [QUAN TRỌNG] INVALIDATE CACHE
    # Khi đã tính toán xong snapshot mới, dữ liệu trên Dashboard cũ đã bị lỗi thời.
    # Ta xóa key cache đi để lần tới Giảng viên F5, hệ thống sẽ tính lại dữ liệu mới nhất.
    cache_key = f"course_pulse_{course_id}"
    cache.delete(cache_key)
    
    print(f"♻️ Cache invalidated for {cache_key}")