from django.db import models
from django.conf import settings
import uuid

# --- TẦNG 1: TỔNG HỢP (AGGREGATES) ---

class CourseProgress(models.Model):
    """
    Bảng tổng hợp (Dashboard): Lưu % hoàn thành của user trong 1 khóa học.
    Giúp query nhanh để hiển thị ra màn hình "My Courses".
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_progress')
    
    # Dùng UUID để loose coupling với app content
    course_id = models.UUIDField(db_index=True) 
    
    # Tính toán: (Số lesson đã xong / Tổng số lesson) * 100
    percent_completed = models.FloatField(default=0.0) 
    
    is_completed = models.BooleanField(default=False) # Xong 100% chưa?
    last_accessed_at = models.DateTimeField(auto_now=True) # Lần cuối vào học

    class Meta:
        unique_together = ('user', 'course_id')
        indexes = [models.Index(fields=['user', 'course_id'])]

class LessonCompletion(models.Model):
    """
    Ghi nhận trạng thái hoàn thành của 1 Lesson.
    Lesson được coi là hoàn thành khi TẤT CẢ (hoặc các block bắt buộc) bên trong nó hoàn thành.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    course_id = models.UUIDField(db_index=True) # Để filter nhanh
    module_id = models.UUIDField(db_index=True)
    lesson_id = models.UUIDField(db_index=True)

    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson_id')


# --- TẦNG 2: CHI TIẾT NỘI DUNG (GRANULAR TRACKING) ---

class BlockCompletion(models.Model):
    """
    (Tương đương mdl_course_modules_completion của Moodle)
    Lưu trạng thái của từng ContentBlock (Video, Text, Image, PDF).
    
    - Nếu là Video: interaction_data lưu timestamp.
    - Nếu là Quiz: Chỉ lưu trạng thái 'passed' hay 'completed'. Chi tiết lưu ở bảng QuizAttempt.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Link tới ContentBlock cụ thể
    block_id = models.UUIDField(db_index=True)
    lesson_id = models.UUIDField(db_index=True) # Denormalized để query nhanh

    # Trạng thái hoàn thành block
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Dữ liệu tương tác (Quan trọng cho Video/SCORM)
    # Ví dụ Video: {"last_timestamp": 120.5, "total_duration": 600, "watched_percent": 20}
    # Ví dụ Text: {"scroll_percentage": 100}
    interaction_data = models.JSONField(default=dict, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'block_id')


# --- TẦNG 3: QUIZ ENGINE (CHUYÊN BIỆT CHO QUIZ) ---
# (Tương đương mdl_quiz_attempts và mdl_question_attempts của Moodle)

class QuizAttempt(models.Model):
    """
    Lưu một LẦN LÀM BÀI (Attempt) của user.
    User có thể làm lại quiz nhiều lần -> Có nhiều rows QuizAttempt cho 1 user/quiz.
    """
    STATUS_CHOICES = [
        ('in_progress', 'Đang làm'),
        ('submitted', 'Đã nộp'),
        ('graded', 'Đã chấm điểm'), # Cho tự luận
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Link tới Quiz (Model Quiz của bạn)
    quiz_id = models.UUIDField(db_index=True)
    
    # Link tới ContentBlock chứa quiz này (để biết user làm quiz ở bài học nào)
    block_id = models.UUIDField(db_index=True, null=True)

    # Điểm số
    score = models.FloatField(default=0.0) # Điểm đạt được
    max_score = models.FloatField(default=10.0) # Tổng điểm tối đa của đề
    is_passed = models.BooleanField(default=False) # Đậu/Rớt (dựa trên grade to pass)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at'] # Lần làm mới nhất lên đầu

class QuestionAnswer(models.Model):
    """
    Lưu câu trả lời chi tiết cho TỪNG CÂU HỎI trong một lần làm bài (Attempt).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    
    # Link tới Question (Model Question của bạn)
    question_id = models.UUIDField(db_index=True)

    # Câu trả lời của user.
    # JSON linh hoạt cho nhiều loại câu hỏi:
    # - Trắc nghiệm đơn: {"selected_id": "a"}
    # - Trắc nghiệm nhiều: {"selected_ids": ["a", "c"]}
    # - Điền từ: {"text": "con mèo"}
    # - Nối: {"pairs": [{"a1": "b2"}, ...]}
    user_answer = models.JSONField(default=dict)

    # Kết quả chấm điểm từng câu
    score = models.FloatField(default=0.0) # Điểm đạt được cho câu này
    is_correct = models.BooleanField(default=False) # Đúng/Sai
    feedback = models.TextField(blank=True, null=True) # Lời phê/Giải thích cụ thể

    class Meta:
        unique_together = ('attempt', 'question_id') # Trong 1 lần làm, mỗi câu chỉ có 1 record