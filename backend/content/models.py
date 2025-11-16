import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

# Create your models here.
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name = ('Category')
        verbose_name_plural = ('Categories')
        ordering = ['name']

    def __str__(self):
        return self.name

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name = ('Tag')
        verbose_name_plural = ('Tags')
        ordering = ['name']

    def __str__(self):
        return self.name

class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name = ('Subject')
        verbose_name_plural = ('Subjects')
        ordering = ['title']

    def __str__(self):
        return self.title

class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    grade = models.CharField(max_length=16, blank=True, null=True)
    published = models.BooleanField(default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_owned')
    categories = models.ManyToManyField(Category, related_name='courses', blank=True)
    tags = models.ManyToManyField(Tag, related_name='courses', blank=True)
    published_at = models.DateTimeField(null=True, blank=True, 
                                        help_text="Timestamp when the course was last published.")
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True, 
                            help_text="URL-friendly version of the title, auto-generated if blank.")

    class Meta:
        verbose_name = ('Course')
        verbose_name_plural = ('Courses')
        ordering = ['title']

    def __str__(self):
        return self.title

class Module(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    position = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = ('Module')
        verbose_name_plural = ('Modules')
        ordering = ['position']

    def __str__(self):
        return f"{self.title} in {self.course}"

class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    position = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    content_type = models.CharField(
        max_length=32,
        default='lesson',
        choices=[('lesson', ('Lesson')), ('exploration', ('Exploration')), ('exercise', ('Exercise')), ('video', ('video'))]
    )
    published = models.BooleanField(default=False)

    class Meta:
        verbose_name = ('Lesson')
        verbose_name_plural = ('Lessons')
        ordering = ['position']

    def __str__(self):
        return self.title

# class LessonVersion(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='versions')
#     version = models.IntegerField(validators=[MinValueValidator(1)])
#     status = models.CharField(
#         max_length=32,
#         default='draft',
#         choices=[('draft', ('Draft')), ('review', ('Review')), ('published', ('Published'))]
#     )
#     author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lesson_versions_authored')
#     content = models.JSONField(default=dict, blank=True)  # Overall content structure
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('lesson', 'version')
#         verbose_name = ('Lesson Version')
#         verbose_name_plural = ('Lesson Versions')
#         ordering = ['-version']

#     def __str__(self):
#         return f"{self.lesson} v{self.version}"
    

class Enrollment(models.Model):
    """
    Model ghi lại việc user nào đã ghi danh vào course nào.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Đảm bảo mỗi user chỉ ghi danh vào 1 course 1 lần
        unique_together = ('user', 'course')
        verbose_name = ('Enrollment')
        verbose_name_plural = ('Enrollments')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"
    

class ContentBlock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='content_blocks', default=1)
    type = models.CharField(
        max_length=32,
        choices=[
            ('text', ('Text')), ('image', ('Image')), ('video', ('Video')),
            ('quiz', ('Quiz')), ('exploration_ref', ('Exploration Reference')),
            ('pdf', ('PDF Document')),   
            ('docx', ('Word Document')),
            ('file', ('File')),
        ]
    )
    position = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    payload = models.JSONField(default=dict)  # e.g., {'text': '...', 'audio_url': '...', 'tts_text': '...', 'captions_url': '...'}

    class Meta:
        verbose_name = ('Content Block')
        verbose_name_plural = ('Content Blocks')
        ordering = ['position']

    def __str__(self):
        # Sửa thành self.lesson
        return f"{self.type} in {self.lesson}"

class Exploration(models.Model):
    # Oppia-style: Interactive state-based lessons.
    id = models.CharField(primary_key=True, max_length=255, editable=False)
    title = models.CharField(max_length=255)
    
    # explorations
    objective = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=8, default='vi')

    # Link with categories and tags
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='explorations')
    tags = models.ManyToManyField(Tag, blank=True, related_name='explorations')

    # Metadata
    init_state_name = models.CharField(max_length=255, blank=True, null=True)
    param_changes = models.JSONField(default=list, blank=True)
    param_specs = models.JSONField(default=dict, blank=True)
    version = models.IntegerField(blank=True, null=True)
    created_on = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)
    blurb = models.TextField(blank=True, null=True)
    author_notes = models.TextField(blank=True, null=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='explorations_owned')
    published = models.BooleanField(default=False)

    class Meta:
        verbose_name = ('Exploration')
        verbose_name_plural = ('Explorations')
        ordering = ['title']

    def __str__(self):
        return self.title

class ExplorationState(models.Model):
    id = models.CharField(primary_key=True, editable=False)
    exploration = models.ForeignKey(Exploration, on_delete=models.CASCADE, related_name='states')
    name = models.CharField(max_length=255)

    # Exploration states
    content_text = models.TextField(blank=True, null=True) # Nội dung text đã trích xuất
    interaction_id = models.CharField(max_length=255, blank=True, null=True)
    card_is_checkpoint = models.BooleanField(default=False)
    linked_skill_id = models.CharField(max_length=255, blank=True, null=True)
    classifier_model_id = models.CharField(max_length=255, blank=True, null=True)
    solicit_answer_details = models.BooleanField(default=False)
    inapplicable_skill_misconception_ids = models.JSONField(default=list, blank=True)

    # state content
    content_id = models.CharField(max_length=255, blank=True, null=True)
    content_html = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = ('Exploration State')
        verbose_name_plural = ('Exploration States')
        ordering = ['exploration', 'name']

    def __str__(self):
        return f"{self.name} in {self.exploration}"
    
class StateMedia(models.Model):
    # state media like images, audio, video, math, etc.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(ExplorationState, on_delete=models.CASCADE, related_name='media')
    content_id = models.CharField(max_length=255, blank=True, null=True)
    media_index = models.IntegerField()
    tag = models.CharField(max_length=255)
    attrs = models.JSONField(default=dict)
    alt = models.TextField(blank=True, null=True)
    filepath = models.CharField(max_length=1024, blank=True, null=True)
    math_value = models.TextField(blank=True, null=True)
    outer_html = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['state', 'media_index']
        unique_together = ('state', 'media_index')
        verbose_name = ('State Media')


class InteractionCustomizationArg(models.Model):
    # customization args for interactions in exploration states
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(ExplorationState, on_delete=models.CASCADE, related_name='customization_args')
    interaction_id = models.CharField(max_length=255, blank=True, null=True)
    arg_name = models.CharField(max_length=255)
    arg_value_json = models.JSONField(default=dict)

    class Meta:
        unique_together = ('state', 'arg_name')
        verbose_name = ('Interaction Argument')


class Hint(models.Model):
    # hints for exploration states
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(ExplorationState, on_delete=models.CASCADE, related_name='hints')
    hint_index = models.IntegerField()
    hint_content_id = models.CharField(max_length=255, blank=True, null=True)
    hint_html = models.TextField(blank=True, null=True)
    hint_text = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['state', 'hint_index']
        unique_together = ('state', 'hint_index')
        verbose_name = ('Hint')


class AnswerGroup(models.Model):
    # answer groups for exploration states
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(ExplorationState, on_delete=models.CASCADE, related_name='answer_groups')
    group_index = models.IntegerField()
    
    # Outcome fields
    outcome_dest = models.CharField(max_length=255, blank=True, null=True) # Tên của state đích
    outcome_dest_if_really_stuck = models.CharField(max_length=255, blank=True, null=True)
    refresher_exploration_id = models.CharField(max_length=255, blank=True, null=True)
    missing_prerequisite_skill_id = models.CharField(max_length=255, blank=True, null=True)
    labelled_as_correct = models.BooleanField(default=False)
    outcome_feedback_html = models.TextField(blank=True, null=True)
    outcome_feedback_text = models.TextField(blank=True, null=True)
    
    # Other fields
    training_data = models.JSONField(default=list, blank=True)
    tagged_skill_misconception_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['state', 'group_index']
        unique_together = ('state', 'group_index')
        verbose_name = ('Answer Group')


class Solution(models.Model):
    # solutions for exploration states
    state = models.OneToOneField(ExplorationState, on_delete=models.CASCADE, related_name='solution', primary_key=True)
    correct_answer = models.JSONField(default=dict, blank=True)
    answer_is_exclusive = models.BooleanField(default=False)
    solution_explanation_html = models.TextField(blank=True, null=True)
    solution_explanation_text = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = ('Solution')


class RuleSpec(models.Model):
    # rule specifications for answer groups
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    answer_group = models.ForeignKey(AnswerGroup, on_delete=models.CASCADE, related_name='rule_specs')
    rule_index = models.IntegerField()
    rule_type = models.CharField(max_length=255)
    inputs_json = models.JSONField(default=dict)

    class Meta:
        ordering = ['answer_group', 'rule_index']
        unique_together = ('answer_group', 'rule_index')
        verbose_name = ('Rule Spec')

class ExplorationTransition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    from_state = models.ForeignKey(ExplorationState, on_delete=models.CASCADE, related_name='from_transitions')
    to_state_name = models.CharField(max_length=255, blank=True, null=True)

    condition_type = models.CharField(max_length=255, default='standard') # 'default' hoặc 'Equals', ...
    condition_data_raw = models.JSONField(default=dict, blank=True)
    feedback_html = models.TextField(blank=True, null=True)
    feedback_text = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = ('Exploration Transition')
        verbose_name_plural = ('Exploration Transitions')
        ordering = ['from_state']

    def __str__(self):
        return f"From {self.from_state} to {self.to_state}"
    

###################################################################################################################################
class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name="Tiêu đề")

    # === 1. THỜI LƯỢNG LÀM BÀI (Time Limit) ===
    # Dùng DurationField là tốt nhất, nó lưu một khoảng thời gian
    time_limit = models.DurationField(
        null=True, 
        blank=True,  # Cho phép không có giới hạn thời gian
        verbose_name="Thời lượng làm bài",
        help_text="Thời gian tối đa cho phép (ví dụ: '00:30:00' cho 30 phút, '01:00:00' cho 1 tiếng)"
    )

    # === 2. THỜI GIAN MỞ ===
    time_open = models.DateTimeField(
        null=True, 
        blank=True,  # Cho phép quiz luôn luôn mở
        verbose_name="Thời gian mở"
    )

    # === 3. THỜI GIAN ĐÓNG (HẠN CHÓT) ===
    time_close = models.DateTimeField(
        null=True, 
        blank=True,  # Cho phép quiz không bao giờ đóng
        verbose_name="Thời gian đóng (hạn chót)"
    )

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

    # === 1. LOẠI CÂU HỎI ===
    # Trường này quyết định cách render và chấm điểm
    type = models.CharField(
        max_length=50,
        choices=QUESTION_TYPES,
        default='multiple_choice_single'
    )

    # === 2. NỘI DUNG CÂU HỎI (Prompt) ===
    # Thay vì 1 trường text, dùng JSONField để chứa text, ảnh, video, audio...
    # Đây chính là nơi bạn giải quyết vấn đề "câu hỏi có ảnh"
    prompt = models.JSONField(
        default=dict,
        blank=True,
        help_text="Nội dung câu hỏi (e.g., {'text': '...', 'image_url': '...'})"
    )

    # === 3. CẤU HÌNH ĐÁP ÁN (Answer Configuration) ===
    # Payload này sẽ lưu các lựa chọn (choices) cho câu trắc nghiệm,
    # hoặc lưu câu trả lời đúng cho câu hỏi trả lời ngắn.
    answer_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Cấu hình đáp án, tùy thuộc vào 'type'"
    )
    
    # === 4. HƯỚNG DẪN / GIẢI THÍCH ===
    hint = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Gợi ý hoặc giải thích đáp án"
    )

    class Meta:
        verbose_name = "Câu hỏi"
        verbose_name_plural = "Các câu hỏi"
        ordering = ['position']

    def __str__(self):
        # Lấy text từ prompt để hiển thị
        prompt_text = self.prompt.get('text', 'Câu hỏi không có tiêu đề')
        return f"[{self.get_type_display()}] {prompt_text[:50]}..."