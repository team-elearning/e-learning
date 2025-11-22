from django.db import models
import uuid
from django.core.validators import MinValueValidator
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation

from custom_account.models import UserModel



class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name="Tiêu đề", null=True, blank=True)
    
    # === CẤU HÌNH THỜI GIAN ===
    time_limit = models.DurationField(null=True, blank=True, verbose_name="Thời lượng làm bài", help_text="Thời gian tối đa cho phép (ví dụ: '00:30:00' cho 30 phút, '01:00:00' cho 1 tiếng)") # null, blank -> cho phép không có giới hạn thời gian
    time_open = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian mở") # null, blank -> cho phép quiz luôn luôn mở
    time_close = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian đóng (hạn chót)") # Cho phép quiz không bao giờ đóng

    QUIZ_MODES = [ # === CHẾ ĐỘ LÀM BÀI ===
        ('exam', 'Kiểm tra (Nghiêm ngặt)'),
        ('practice', 'Ôn luyện (Thoải mái)'),
    ]
    mode = models.CharField(choices=QUIZ_MODES, default='exam', max_length=20)
    
    max_attempts = models.PositiveIntegerField(null=True, blank=True, help_text="Để trống nếu cho làm thoải mái") # Số lần làm bài: null = không giới hạn (cho mode Practice)
    pass_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # === CẤU HÌNH RANDOM ===
    questions_count = models.IntegerField(default=10, help_text="Số lượng câu hỏi hiển thị cho mỗi lần làm bài. 0 = Hiển thị tất cả câu hỏi hiện có.")
    shuffle_questions = models.BooleanField(default=True, verbose_name="Đảo câu hỏi")

    GRADING_METHOD = [ # Cách tính điểm (Khi làm nhiều lần)
        ('highest', 'Lấy điểm cao nhất'), # Thường dùng cho Practice
        ('average', 'Lấy điểm trung bình'),
        ('first', 'Lấy lần đầu tiên'),    # Thường dùng cho Exam
        ('last', 'Lấy lần cuối cùng'),
    ]
    grading_method = models.CharField(choices=GRADING_METHOD, default='highest', max_length=20)

    # Xem lại bài làm (Review Options)
    show_correct_answer = models.BooleanField(default=True, verbose_name="Hiện đáp án sau khi nộp")
    description = models.TextField(blank=True, verbose_name="Mô tả / Hướng dẫn")
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='quiz_owned')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    files = GenericRelation('media.UploadedFile')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Bài trắc nghiệm"
        verbose_name_plural = "Các bài trắc nghiệm"



class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice_single', 'Trắc nghiệm - Chọn 1'),
        ('multiple_choice_multi', 'Trắc nghiệm - Chọn nhiều'),
        ('true_false', 'Đúng / Sai'),
        ('short_answer', 'Trả lời ngắn'),
        ('fill_in_the_blank', 'Điền vào chỗ trống'),
        ('matching', 'Nối cặp'),
        ('essay', 'Tự luận'),
        # Thêm bất cứ loại nào bạn muốn trong tương lai
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    position = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    type = models.CharField(max_length=50, choices=QUESTION_TYPES, default='multiple_choice_single')

    # Dùng JSON để lưu nội dung cho linh hoạt (Text, Ảnh, Các lựa chọn A,B,C,D)
    # Cấu trúc: { "content": "...", "image": "...", "options": [{"id": "A", "text": "..."}, ...] }
    prompt = models.JSONField(default=dict, blank=True, help_text="Nội dung câu hỏi (e.g., {'text': '...', 'image_url': '...'})")

    # Cấu trúc: { "correct_ids": ["A"], "explanation": "..." }
    answer_payload = models.JSONField(default=dict, blank=True, help_text="Cấu hình đáp án, tùy thuộc vào 'type'")
    hint = models.JSONField(default=dict, blank=True, help_text="Gợi ý hoặc giải thích đáp án")
    files = GenericRelation('media.UploadedFile')

    class Meta:
        verbose_name = "Câu hỏi"
        verbose_name_plural = "Các câu hỏi"
        ordering = ['position']

    def __str__(self):
        # Lấy text từ prompt để hiển thị
        prompt_text = self.prompt.get('text', 'Câu hỏi không có tiêu đề')
        return f"[{self.get_type_display()}] {prompt_text[:50]}..."
    


class QuizAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    
    # Snapshot đề thi: Lưu danh sách ID câu hỏi ĐÃ RANDOM cho riêng lần này
    # Để user vào lại vẫn thấy đúng đề đó, thứ tự đó.
    questions_order = models.JSONField(default=list, help_text="Danh sách ID các câu hỏi được chọn ngẫu nhiên cho lần làm bài này")

    # Thời điểm bắt đầu & nộp bài
    time_start = models.DateTimeField(auto_now_add=True)
    time_submitted = models.DateTimeField(null=True, blank=True)

    score = models.DecimalField(max_digits=5, decimal_places=2, null=True) # Điểm số (tính sau khi nộp)

    # Lưu trạng thái làm bài hiện tại (để tính năng Resume Learning)
    # Ví dụ: user đang làm đến câu index số 5
    current_question_index = models.IntegerField(default=0)

    STATUS_CHOICES = [
        ('in_progress', 'Đang làm bài'),
        ('completed', 'Đã nộp'),
        ('overdue', 'Quá hạn (Chưa nộp nhưng hết giờ)'), 
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')

    class Meta:
        ordering = ['-time_start']


class UserAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    selected_options = models.JSONField(default=dict, help_text="Dữ liệu câu trả lời của user") # Dùng JSON vì có thể là chọn A, chọn [A, C], hoặc điền text.
    is_correct = models.BooleanField(null=True, default=None) # Có đúng không? (True/False/None - chưa chấm)
    score_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0) # Điểm đạt được cho riêng câu này

    class Meta:
        unique_together = ('attempt', 'question') # Mỗi lần làm bài, 1 câu chỉ trả lời 1 lần
