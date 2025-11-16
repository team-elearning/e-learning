import os
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from content.models import Course


def user_directory_path(instance, filename):
    """
    Tạo đường dẫn upload file có cấu trúc, dựa trên component và người dùng.
    VD: course_thumbnail/user_1/ten_file.jpg
    VD: lesson_material/user_1/ten_file.pdf
    """
    
    # 1. Lấy component (dùng 'general' nếu bị trống)
    # instance.component sẽ là 'course_thumbnail', 'lesson_material', v.v.
    component_path = instance.component or 'general'
    
    # 2. Lấy ID người dùng (dùng 'unknown' nếu vì lý do nào đó user bị null)
    user_id = 'unknown'
    if instance.uploaded_by:
        user_id = instance.uploaded_by.id
        
    user_path = f'user_{user_id}'

    # 4. Trích xuất tên file và extension
    # (Để làm sạch tên file nếu cần)
    filename_base, filename_ext = os.path.splitext(filename)
    
    # Có thể dùng 'uuid.uuid4()' thay cho 'filename' ở đây nếu muốn
    # đảm bảo tên file không bao giờ trùng lặp và an toàn.
    filename = f"{uuid.uuid4()}{filename_ext}"

    # Trả về cấu trúc thư mục mới
    return os.path.join(component_path, user_path, filename)

class FileStatus(models.TextChoices):
    STAGING = 'staging', 'Đang chờ' 
    COMMITTED = 'committed', 'Đã sử dụng'

# Create your models here.
class UploadedFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    file = models.FileField(upload_to=user_directory_path)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=FileStatus.choices,
        default=FileStatus.STAGING, # Mặc định là staging
        db_index=True
    )
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )

    # Dùng để phân loại (ví dụ: 'course_thumbnail', 'lesson_material', 'user_avatar')
    component = models.CharField(max_length=100, db_index=True, blank=True, null=True)

    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True, # Cho phép file staging (chưa commit)
        blank=True
    )
    object_id = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        db_index=True
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.original_filename or self.file.name

    @property
    def url(self):
        if self.file:
            return self.file.url
        return None
    

