import uuid
from django.contrib.postgres.fields import ArrayField # Cần PostgreSQL
from django.db import models

from content.models import Course



class CourseEmbedding(models.Model):
    """
    Lưu trữ Vector của khóa học để phục vụ AI Semantic Search.
    Thay thế cho file .pkl.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.OneToOneField('content.Course', on_delete=models.CASCADE, related_name='embedding')
    
    # Vector của OpenAI text-embedding-3-small có kích thước 1536 dimensions
    # Lưu dưới dạng mảng số thực (float array)
    vector = ArrayField(models.FloatField(), size=1536, blank=True, null=True)
    
    # Lưu lại hash hoặc raw text để check xem nội dung có thay đổi không (cần update vector ko)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Course Embedding'
        verbose_name_plural = 'Course Embeddings'

    def __str__(self):
        return f"Vector for {self.course.title}"