from django.db import models
import uuid
from django.core.validators import MinValueValidator
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation

from custom_account.models import UserModel



QUIZ_MODES = [ # === CHẾ ĐỘ LÀM BÀI ===
        ('exam', 'Kiểm tra (Nghiêm ngặt)'),
        ('practice', 'Ôn luyện (Thoải mái)'),
        ('quiz', 'Quiz'),
    ]


class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name="Tiêu đề", null=True, blank=True)
    
    # === CẤU HÌNH THỜI GIAN ===
    mode = models.CharField(choices=QUIZ_MODES, default='exam', max_length=20)
    time_limit = models.DurationField(null=True, blank=True, verbose_name="Thời lượng làm bài", help_text="Thời gian tối đa cho phép (ví dụ: '00:30:00' cho 30 phút, '01:00:00' cho 1 tiếng)") # null, blank -> cho phép không có giới hạn thời gian
    time_open = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian mở") # null, blank -> cho phép quiz luôn luôn mở
    time_close = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian đóng (hạn chót)") # Cho phép quiz không bao giờ đóng

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

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Bài trắc nghiệm"
        verbose_name_plural = "Các bài trắc nghiệm"


QUESTION_TYPES = [
    # --- NHÓM CƠ BẢN (Udemy/Coursera) ---
    ('multiple_choice_single', 'Trắc nghiệm - Chọn 1'),
    ('multiple_choice_multi', 'Trắc nghiệm - Chọn nhiều'),
    ('true_false', 'Đúng / Sai'), # Thực chất là biến thể của Single, nhưng tách ra để Frontend vẽ UI khác (Toggle switch)
    
    # --- NHÓM TỰ LUẬN/TEXT ---
    ('short_answer', 'Trả lời ngắn (Text)'), # So sánh chuỗi chính xác hoặc chứa từ khóa
    ('essay', 'Tự luận (Chấm tay)'), # Giáo viên phải vào chấm điểm thủ công
    
    # --- NHÓM NÂNG CAO (Moodle/Khan Style) ---
    ('fill_in_the_blank', 'Điền từ (Cloze)'), # Điền vào nhiều chỗ trống trong 1 đoạn văn
    ('matching', 'Nối cặp'),                  # Nối cột A với cột B
    ('ordering', 'Sắp xếp thứ tự'),           # Kéo thả sắp xếp trên dưới
    ('numeric', 'Số học'),                    # So sánh toán học (sai số, phân số)
]

class Question(models.Model):
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
    
