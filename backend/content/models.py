import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

# Create your models here.
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
        choices=[('lesson', ('Lesson')), ('exploration', ('Exploration')), ('exercise', ('Exercise'))]
    )
    published = models.BooleanField(default=False)

    class Meta:
        verbose_name = ('Lesson')
        verbose_name_plural = ('Lessons')
        ordering = ['position']

    def __str__(self):
        return self.title

class LessonVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='versions')
    version = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(
        max_length=32,
        default='draft',
        choices=[('draft', ('Draft')), ('review', ('Review')), ('published', ('Published'))]
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='lesson_versions_authored')
    content = models.JSONField(default=dict, blank=True)  # Overall content structure
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lesson', 'version')
        verbose_name = ('Lesson Version')
        verbose_name_plural = ('Lesson Versions')
        ordering = ['-version']

    def __str__(self):
        return f"{self.lesson} v{self.version}"

class ContentBlock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson_version = models.ForeignKey(LessonVersion, on_delete=models.CASCADE, related_name='content_blocks')
    type = models.CharField(
        max_length=32,
        choices=[
            ('text', ('Text')), ('image', ('Image')), ('video', ('Video')),
            ('quiz', ('Quiz')), ('exploration_ref', ('Exploration Reference'))
        ]
    )
    position = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    payload = models.JSONField(default=dict)  # e.g., {'text': '...', 'audio_url': '...', 'tts_text': '...', 'captions_url': '...'}

    class Meta:
        verbose_name = ('Content Block')
        verbose_name_plural = ('Content Blocks')
        ordering = ['position']

    def __str__(self):
        return f"{self.type} in {self.lesson_version}"

class Exploration(models.Model):
    # Oppia-style: Interactive state-based lessons.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='explorations_owned')
    language = models.CharField(max_length=8, default='vi')
    published = models.BooleanField(default=False)

    class Meta:
        verbose_name = ('Exploration')
        verbose_name_plural = ('Explorations')

    def __str__(self):
        return self.title

class ExplorationState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exploration = models.ForeignKey(Exploration, on_delete=models.CASCADE, related_name='states')
    name = models.CharField(max_length=255)
    content = models.JSONField(default=dict)  # Prompt, text, media
    interaction = models.JSONField(default=dict)  # Input schema, hints

    class Meta:
        verbose_name = ('Exploration State')
        verbose_name_plural = ('Exploration States')

    def __str__(self):
        return f"{self.name} in {self.exploration}"

class ExplorationTransition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exploration = models.ForeignKey(Exploration, on_delete=models.CASCADE, related_name='transitions')
    from_state = models.ForeignKey(ExplorationState, on_delete=models.CASCADE, related_name='from_transitions')
    to_state = models.ForeignKey(ExplorationState, on_delete=models.CASCADE, related_name='to_transitions')
    condition = models.JSONField(default=dict)  # Rules, classifiers

    class Meta:
        verbose_name = ('Exploration Transition')
        verbose_name_plural = ('Exploration Transitions')

    def __str__(self):
        return f"From {self.from_state} to {self.to_state}"