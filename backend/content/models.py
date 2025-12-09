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
    # files = GenericRelation('media.UploadedFile')
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