from django.db import models
from django.conf import settings
import uuid

from content.models import Course, ContentBlock, Enrollment, Module, Lesson
from quiz.models import Quiz, Question, QUESTION_TYPES, QUIZ_MODES



class ModuleCompletion(models.Model):
    """
    CHECKPOINT: Dùng để xử lý logic 'Phải xong Module 1 mới mở Module 2'.
    Không lưu interaction_data, chỉ lưu trạng thái Done.
    """
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='completed_modules')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('enrollment', 'module')


class LessonCompletion(models.Model):
    """
    CHECKPOINT: Dùng để xử lý logic 'Phải xong Lesson 1 mới mở Lesson 2'.
    """
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='completed_lessons', null=True, blank=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('enrollment', 'lesson')


class UserBlockProgress(models.Model):
    """
    Lưu trạng thái học tập của User tại một Block cụ thể.
    Đây là bảng đích cho API Heartbeat.
    Chỉ tạo record khi user CHẠM vào block (Lazy Creation).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='block_accesses', null=True, blank=True)

    # Denormalization: Lưu thẳng ID để đỡ phải join bảng Enrollment
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='block_progress')
    block = models.ForeignKey(ContentBlock, on_delete=models.CASCADE, related_name='user_progress')
    
    # --- TRẠNG THÁI ---
    is_completed = models.BooleanField(default=False) 
    completed_at = models.DateTimeField(null=True, blank=True)

    # --- HEARTBEAT DATA ---
    # Với Video: {"timestamp": 125, "watch_rate": 0.8}
    # Với Text: {"scroll": "bottom"}
    interaction_data = models.JSONField(default=dict, blank=True)
    
    # Thời gian user dành cho bài này (giây) - Phục vụ Analytics
    time_spent_seconds = models.PositiveIntegerField(default=0)

    last_accessed = models.DateTimeField(auto_now=True) # Tự động cập nhật mỗi khi heartbeat gọi

    class Meta:
        unique_together = ('enrollment', 'block')
        indexes = [
            # Index quan trọng để tính %: Đếm số bài đã xong của 1 enrollment
            models.Index(fields=['enrollment', 'is_completed']), 
        ]

    def __str__(self):
        return f"{self.user} - {self.block} - {self.last_accessed}"


STATUS_CHOICES = [
        ('in_progress', 'Đang làm'),
        ('submitted', 'Đã nộp'),
        ('graded', 'Đã chấm điểm'), # Cho tự luận
    ]

class QuizAttempt(models.Model):
    """
    Lưu một LẦN LÀM BÀI (Attempt) của user.
    User có thể làm lại quiz nhiều lần -> Có nhiều rows QuizAttempt cho 1 user/quiz.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts', null=True, blank=True)

    # === NGỮ CẢNH (CONTEXT) - ĐÂY LÀ CHÌA KHÓA ===
    # Trường hợp 1: Làm trong khóa học
    # Link tới Enrollment để check quyền hạn và tính điểm tổng kết khóa
    enrollment = models.ForeignKey('content.Enrollment', on_delete=models.CASCADE, null=True, blank=True, related_name='quiz_attempts')

    # Link tới Lesson cụ thể (ContentBlock) để biết đang học bài nào
    # Khi làm xong, trigger update vào bảng UserBlockAccess (Nhóm 1)
    content_block = models.ForeignKey('content.ContentBlock', on_delete=models.SET_NULL, null=True, blank=True)

    # Trường hợp 2: Làm tự do (Practice) -> 2 trường trên sẽ là NULL.
    # Hệ thống chỉ cần check user và quiz_id.

    # === SNAPSHOT (LƯU VẾT) ===
    # Lưu lại mode lúc làm bài (đề phòng giáo viên đổi config sau này)
    attempt_mode = models.CharField(max_length=20, choices=QUIZ_MODES, default='exam')

    # Danh sách ID câu hỏi theo thứ tự đã random
    questions_order = models.JSONField(default=list)

    # === KẾT QUẢ ===
    score = models.FloatField(default=0.0) # Điểm đạt được
    max_score = models.FloatField(default=10.0) # Tổng điểm tối đa của đề
    is_passed = models.BooleanField(default=False) # Đậu/Rớt (dựa trên grade to pass)

    # === TRẠNG THÁI ===
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    current_question_index = models.IntegerField(default=0) # Resume learning

    time_start = models.DateTimeField(auto_now_add=True)
    time_submitted = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-time_start']
        indexes = [
            models.Index(fields=['user', 'quiz']), # Để tìm lịch sử làm bài
            models.Index(fields=['enrollment']),   # Để tính điểm trung bình khóa học
        ]

    @property
    def is_in_course(self):
        """Helper để check xem bài này làm trong khóa học hay làm chơi"""
        return self.enrollment_id is not None


class QuestionAnswer(models.Model):
    """
    Lưu câu trả lời chi tiết cho TỪNG CÂU HỎI trong một lần làm bài (Attempt).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers', null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True)

    # Snapshot loại câu hỏi (để render view kết quả nhanh hơn)
    question_type = models.CharField(choices=QUESTION_TYPES, max_length=50, blank=True)

    # Câu trả lời (JSON để support nhiều loại)
    # Trắc nghiệm: {"selected_ids": ["uuid-1", "uuid-2"]}
    # Điền từ: {"text": "machine learning"}
    # Kéo thả: {"pairs": {"A": "1", "B": "2"}}
    answer_data = models.JSONField(default=dict)

    is_flagged = models.BooleanField(default=False)

    # Kết quả chấm điểm từng câu
    score = models.FloatField(default=0.0) # Điểm đạt được cho câu này
    is_correct = models.BooleanField(default=False) # Đúng/Sai
    
    feedback = models.TextField(blank=True, null=True) # Lời phê/Giải thích cụ thể

    class Meta:
        unique_together = ('attempt', 'question')


class UserCertificate(models.Model):
    """
    Lưu trữ chứng chỉ đã cấp cho user.
    Chỉ tạo ra khi CourseProgress.percent_completed = 100% HOẶC Pass Final Exam.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Quan hệ
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE) # Link để truy xuất ngày bắt đầu/kết thúc

    # Định danh chứng chỉ (Để nhà tuyển dụng verify)
    # Ví dụ: CERT-2025-ABCD-1234
    certificate_code = models.CharField(max_length=50, unique=True, db_index=True)
    
    # File PDF (Lưu đường dẫn file đã generate)
    file = models.FileField(upload_to='certificates/%Y/%m/', null=True, blank=True)
    
    # Snapshot dữ liệu tại thời điểm cấp (đề phòng user đổi tên sau này)
    issued_to_name = models.CharField(max_length=255, help_text="Tên hiển thị trên bằng")
    issued_at = models.DateTimeField(auto_now_add=True)

    # Trạng thái (Phòng trường hợp thu hồi bằng)
    is_valid = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'course') # Mỗi khóa chỉ cấp 1 bằng
        ordering = ['-issued_at']

    def __str__(self):
        return f"Certificate {self.certificate_code} - {self.user.username}"
    

class CourseReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)]) # 1-5 sao
    content = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_visible = models.BooleanField(default=True) # Để ẩn review spam

    class Meta:
        unique_together = ('user', 'course')