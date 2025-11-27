import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.contrib.contenttypes.fields import GenericRelation

from quiz.models import Quiz


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
    published_at = models.DateTimeField(null=True, blank=True, 
                                        help_text="Timestamp when the course was last published.")
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True, 
                            help_text="URL-friendly version of the title, auto-generated if blank.")
    created_at = models.DateTimeField(auto_now_add=True) # Tự động lưu lúc tạo
    updated_at = models.DateTimeField(auto_now=True)     # Tự động lưu lúc sửa
    files = GenericRelation('media.UploadedFile')

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
    files = GenericRelation('media.UploadedFile')

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
    # content_type = models.CharField(
    #     max_length=32,
    #     default='lesson',
    #     choices=[('lesson', ('Lesson')), ('exercise', ('Exercise')), ('video', ('video'))]
    # )
    # published = models.BooleanField(default=True)
    files = GenericRelation('media.UploadedFile')

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
            ('text', ('Text')), ('image', ('Image')), ('video', ('Video')),
            ('quiz', ('Quiz')), 
            ('pdf', ('PDF Document')),   
            ('docx', ('Word Document')),
            ('file', ('File')),
        ]
    )
    position = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    payload = models.JSONField(default=dict)  # e.g., {'text': '...', 'audio_url': '...', 'tts_text': '...', 'captions_url': '...'}
    quiz_ref = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE, # Hoặc CASCADE nếu bạn muốn
        null=True,
        blank=True,
        related_name='content_blocks',
        help_text="Tham chiếu đến một Quiz nếu type='quiz'"
    )
    files = GenericRelation('media.UploadedFile')

    class Meta:
        verbose_name = ('Content Block')
        verbose_name_plural = ('Content Blocks')
        ordering = ['position']

    def __str__(self):
        # Sửa thành self.lesson
        return f"{self.type} in {self.lesson}"