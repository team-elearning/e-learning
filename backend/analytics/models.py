from django.db import models
from django.conf import settings
import uuid



# Các hành động chuẩn (Verbs) để AI dễ phân loại
ACTION_VERBS = [
    # --- NHÓM 1: AUTH & SYSTEM ---
    ('LOGIN', 'Đăng nhập'),
    ('LOGOUT', 'Đăng xuất'),
    ('REGISTER', 'Đăng ký tài khoản'),
    ('UPDATE_PROFILE', 'Cập nhật hồ sơ'),

    # --- NHÓM 2: COURSE LIFECYCLE (Funnel) ---
    ('VIEW_COURSE', 'Xem trang giới thiệu khóa học'),
    # ('ADD_TO_WISHLIST', 'Thêm vào yêu thích'),
    # ('ADD_TO_CART', 'Thêm vào giỏ hàng'),
    ('ENROLL', 'Ghi danh khóa học'),
    ('UNENROLL', 'Hủy ghi danh'),
    ('COURSE_COMPLETE', 'Hoàn thành khóa học'), # Sự kiện quan trọng để cấp chứng chỉ
    # ('CERTIFICATE_ISSUE', 'Được cấp chứng chỉ'),
    # ('DOWNLOAD_CERTIFICATE', 'Tải chứng chỉ'),

    # --- NHÓM 3: LEARNING FLOW (Bài học) ---
    ('VIEW_LESSON', 'Xem bài học'),
    ('LESSON_COMPLETE', 'Hoàn thành bài học'), # Đánh dấu tick xanh
    ('DOWNLOAD_RESOURCE', 'Tải tài liệu đính kèm'),
    # ('NOTE_CREATE', 'Tạo ghi chú'), # Udemy feature
    
    # Nhóm Video (Quan trọng để tính độ tập trung)
    ('VIDEO_PLAY', 'Bắt đầu xem'),
    ('VIDEO_PAUSE', 'Tạm dừng'),
    ('VIDEO_SEEK', 'Tua video'),
    ('VIDEO_COMPLETE', 'Xem hết video'),
    ('VIDEO_SPEED_CHANGE', 'Đổi tốc độ'), # Payload: {speed: 1.5}
    ('LEARNING_SESSION', 'Học được bao lâu'), 
    
    # Nhóm Quiz (Quan trọng để phát hiện gian lận hoặc struggle)
    ('QUIZ_START', 'Bắt đầu làm bài'),
    ('QUIZ_RESUME', 'Làm tiếp bài đang dở'),
    ('QUESTION_VIEW', 'Xem câu hỏi'), # Để đo thời gian dwell time trên từng câu
    ('QUESTION_ANSWER_SAVE', 'Lưu nháp câu trả lời'),
    ('QUIZ_SUBMIT', 'Nộp bài'),
    # ('ASSIGNMENT_UPLOAD', 'Nộp bài tập tự luận'),
    ('QUIZ_REVIEW', 'Xem lại bài đã chấm'),
    
    # Nhóm System
    ('SEARCH', 'Tìm kiếm'),
    ('DOWNLOAD_RESOURCE', 'Tải tài liệu'),

    # --- NHÓM 3: TƯƠNG TÁC (Social - Optional) ---
    ('DISCUSSION_POST', 'Đăng thảo luận'),
    ('NOTE_CREATE', 'Tạo ghi chú'),
    ('RATING_SUBMIT', 'Đánh giá khóa học'),

    # --- NHÓM 4: GAMIFICATION (Để debug/audit) ---
    ('STREAK_UPDATE', 'Cập nhật chuỗi'),
    ('ITEM_PURCHASE', 'Mua vật phẩm'),
]

class UserActivityLog(models.Model):
    """
    Bảng lưu vết chân số (Digital Footprint).
    Dữ liệu này sẽ rất lớn, cần đánh index kỹ.
    """
    id = models.BigAutoField(primary_key=True) # Dùng BigInt thay vì UUID để insert nhanh hơn và tiết kiệm dung lượng index
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_logs')
    
    # 1. AI (Actor): Là user rồi.
    
    # 2. Verb (Làm gì):
    action = models.CharField(max_length=50, choices=ACTION_VERBS, db_index=True)
    
    # 3. Object (Trên cái gì):
    # Thay vì dùng GenericForeignKey (chậm), ta lưu ID và Type thủ công
    # Ví dụ: entity_type='course', entity_id='uuid-cua-khoa-hoc'
    entity_type = models.CharField(max_length=50, blank=True, null=True, db_index=True) 
    entity_id = models.CharField(max_length=100, blank=True, null=True)
    
    # 4. Context (Bối cảnh):
    # Lưu chi tiết: Tua từ giây 10 đến giây 50? Dùng trình duyệt gì? IP nào?
    payload = models.JSONField(default=dict, blank=True)
    
    # 5. Thời gian
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Session ID: Để gom nhóm các hành động trong 1 buổi học
    # Frontend sẽ sinh ra 1 session_id mỗi khi user F5 hoặc login
    session_id = models.CharField(max_length=50, blank=True, null=True)

    # [NEW] Denormalization: Lưu course_id trực tiếp để query Dashboard/Analytics siêu nhanh.
    # Frontend hoặc API record phải chịu khó gửi kèm ID này lên.
    course_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            # Index kép để query nhanh: "Tìm tất cả hành động VIDEO của User A"
            models.Index(fields=['user', 'action']),
            # Index cho việc dọn dẹp log cũ
            models.Index(fields=['timestamp']),

            # [NEW] Index quan trọng nhất cho Analytics
            # Giúp lệnh filter(course_id=X, timestamp>Y) chạy trong tíc tắc
            models.Index(fields=['course_id', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"
    

class StudentSnapshot(models.Model):
    """
    Bảng lưu kết quả 'khám sức khỏe' học tập định kỳ.
    """
    id = models.BigAutoField(primary_key=True)
    
    # Định danh
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='risk_snapshots')
    course = models.ForeignKey('content.Course', on_delete=models.CASCADE, related_name='student_risks')
    
    # Các chỉ số (Metrics) đã tính toán
    engagement_score = models.FloatField(default=0.0)   # 0-10
    performance_score = models.FloatField(default=0.0)  # 0-10
    days_inactive = models.IntegerField(default=0)      # Số ngày vắng
    
    # Kết luận
    RISK_LEVELS = [
        ('low', 'An toàn'),
        ('medium', 'Cần chú ý'),
        ('high', 'Rủi ro cao'),
        ('critical', 'Bỏ học')
    ]
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS, db_index=True)
    
    # Hành động gợi ý (Lưu lại để sau này check xem Admin có làm theo AI không)
    suggested_action = models.CharField(max_length=50, blank=True)
    ai_message = models.TextField(blank=True) # Lý do tại sao AI đánh giá như vậy
    
    # Thời điểm tính toán (Snapshotted at)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Index để query nhanh Dashboard: "Lấy risk mới nhất của User A trong Course B"
            models.Index(fields=['user', 'course', '-created_at']),
            models.Index(fields=['course', 'risk_level']), # Lọc danh sách học viên yếu kém
        ]

    def __str__(self):
        return f"{self.user} - {self.course} - {self.risk_level}"


class CourseAnalyticsLog(models.Model):
    """
    Bảng này lưu lịch sử chạy phân tích (Audit Trail).
    Giúp trả lời: "Tại sao hôm qua không có dữ liệu? À do Job bị lỗi."
    """
    id = models.BigAutoField(primary_key=True)
    course = models.ForeignKey('content.Course', on_delete=models.CASCADE, related_name='analytics_logs')
    
    # Kết quả thực thi
    total_students = models.IntegerField(default=0)
    processed_count = models.IntegerField(default=0)
    
    # Trạng thái
    STATUS_CHOICES = [
        ('success', 'Thành công'),
        ('failed', 'Thất bại'),
        ('partial', 'Một phần (Có lỗi nhỏ)')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    
    # Thời gian chạy (Performance monitoring)
    execution_time_seconds = models.FloatField(default=0.0)
    
    # Nếu lỗi thì lưu traceback vào đây
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', '-created_at']) # Để query "Lần chạy gần nhất"
        ]


class QuizStatisticSnapshot(models.Model):
    """
    Lưu tổng hợp kết quả phân tích của 1 bài thi tại thời điểm cụ thể.
    Tương đương: QuizQualityDomain
    """
    id = models.BigAutoField(primary_key=True)
    quiz = models.ForeignKey('quiz.Quiz', on_delete=models.CASCADE, related_name='statistics')
    
    # Metadata
    total_attempts = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    
    # Những chỉ số nâng cao (Moodle style)
    standard_deviation = models.FloatField(default=0.0, help_text="Độ lệch chuẩn")
    median_score = models.FloatField(default=0.0)
    
    # Thời điểm tính toán (quan trọng để biết data có cũ không)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-calculated_at']
        indexes = [
            models.Index(fields=['quiz', '-calculated_at']),
        ]


class QuestionStatisticSnapshot(models.Model):
    """
    Lưu chỉ số chi tiết cho TỪNG câu hỏi trong lần phân tích đó.
    Tương đương: QuestionAnalysisDomain
    """
    id = models.BigAutoField(primary_key=True)
    quiz_stat = models.ForeignKey(QuizStatisticSnapshot, on_delete=models.CASCADE, related_name='questions')
    question = models.ForeignKey('quiz.Question', on_delete=models.CASCADE)
    
    # Snapshot nội dung câu hỏi (đề phòng GV sửa đề sau này)
    prompt_text_snapshot = models.TextField(blank=True) 
    
    # Các chỉ số
    total_attempts = models.IntegerField(default=0)
    correct_ratio = models.FloatField(default=0.0)        # Difficulty (p)
    discrimination_index = models.FloatField(default=0.0) # Discrimination (d)
    
    # Lưu phân phối đáp án dưới dạng JSON
    # VD: {'A': 15.5, 'B': 80.0, 'C': 4.5}
    option_distribution = models.JSONField(default=dict)
    
    status = models.CharField(max_length=20) # 'good', 'check_key'...
    recommendation = models.TextField(blank=True)

    class Meta:
        # Index để query nhanh: "Lấy thống kê của câu hỏi X trong lần tính mới nhất"
        indexes = [
            models.Index(fields=['question', 'quiz_stat']),
        ]


