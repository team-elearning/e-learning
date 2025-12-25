import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.contrib.contenttypes.fields import GenericRelation

from quiz.models import Quiz
from core.custom_storages import PublicMediaStorage


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
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    grade = models.CharField(max_length=16, blank=True, null=True)
    published = models.BooleanField(default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_owned')
    categories = models.ManyToManyField(Category, related_name='courses', blank=True)
    tags = models.ManyToManyField(Tag, related_name='courses', blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True, 
                            help_text="URL-friendly version of the title, auto-generated if blank.")
    price = models.DecimalField(max_digits=12, decimal_places=0, default=0) # Ví dụ: 500.000 VND
    currency = models.CharField(max_length=10, default='VND')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    published_at = models.DateTimeField(null=True, blank=True, 
                                        help_text="Timestamp when the course was last published.")
    thumbnail = models.ImageField(upload_to='course_thumbnails/', storage=PublicMediaStorage(), blank=True, null=True)

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at'] # Mặc định nên để bài mới nhất lên đầu
        
        # Index để search nhanh hơn
        indexes = [
            models.Index(fields=['published', 'grade']), 
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return self.title

    # Helper check xem khóa học có free không
    @property
    def is_free(self):
        return self.price == 0


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


RISK_LEVELS = [
        ('low', 'An toàn'),
        ('medium', 'Cần chú ý'),
        ('high', 'Rủi ro cao'),
        ('critical', 'Bỏ học')
    ]

class Enrollment(models.Model):
    """
    Model ghi lại việc user nào đã ghi danh vào course nào.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    # --- TIẾN ĐỘ TỔNG HỢP (Aggregation) ---
    # Cache lại % để hiển thị Dashboard nhanh, không cần count(*) mỗi lần load
    percent_completed = models.FloatField(default=0.0) 
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_accessed_at = models.DateTimeField(auto_now=True)

    # [NEW] Lưu bài học đang học dở. Update mỗi khi user touch vào bài học.
    # Giúp Dashboard query 1 phát ra luôn, khỏi cần scan bảng log.
    current_block = models.ForeignKey(
        'ContentBlock', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='current_enrollments'
    )

    current_engagement_score = models.FloatField(default=0.0, db_index=True) # Index để sort Top Course nhanh
    current_performance_score = models.FloatField(default=0.0)
    current_days_inactive = models.IntegerField(default=0)

    current_risk_level = models.CharField(
        max_length=20, 
        choices=RISK_LEVELS, 
        default='low', 
        db_index=True 
    )

    class Meta:
        unique_together = ('user', 'course')
        indexes = [
            models.Index(fields=['user', 'course']), # Query check quyền học
            models.Index(fields=['user', '-last_accessed_at']), # Query dashboard
            models.Index(fields=['course', 'current_risk_level']),
            models.Index(fields=['course', 'current_engagement_score']),
        ]
      

class ContentBlock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True, null=True, help_text="Tiêu đề hiển thị trên mục lục (VD: Video hướng dẫn)")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='content_blocks', default=1)
    type = models.CharField(
        max_length=32,
        choices=[
            ('rich_text', ('Rich Text')),
            ('video', ('Video')),
            ('pdf', ('PDF Document')),   
            ('docx', ('Word Document')),
            ('file', ('File')),
            ('quiz', ('Quiz')), 
            ('audio', ('Audio'))
        ]
    )
    duration = models.PositiveIntegerField(default=0, help_text="Thời lượng tính bằng giây")
    position = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    payload = models.JSONField(default=dict)  
    quiz_ref = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE, # Hoặc CASCADE nếu bạn muốn
        null=True,
        blank=True,
        related_name='content_blocks',
        help_text="Tham chiếu đến một Quiz nếu type='quiz'"
    )

    class Meta:
        verbose_name = ('Content Block')
        verbose_name_plural = ('Content Blocks')
        ordering = ['position']

    def __str__(self):
        # Sửa thành self.lesson
        return f"{self.type} in {self.lesson}"