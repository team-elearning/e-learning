import os
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models.signals import post_delete
from django.dispatch import receiver
import mimetypes

from content.models import Course



def user_directory_path(instance, filename):
    import uuid
    from datetime import datetime
    
    # 1. Component
    component = instance.component or "general"
    
    # 2. Tạo tên file
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    
    # Tổ chức theo Component và Thời gian.
    today = datetime.now()
    return f"media/{component}/{today.year}/{today.month}/{filename}"


class FileStatus(models.TextChoices):
    STAGING = 'staging', 'Đang chờ' 
    COMMITTED = 'committed', 'Đã sử dụng'

class Component(models.TextChoices):
        # Public Components (Ai cũng xem được)
        COURSE_THUMBNAIL = 'course_thumbnail', 'Ảnh bìa khóa học'
        USER_AVATAR = 'user_avatar', 'Avatar người dùng'
        SITE_LOGO = 'site_logo', 'Logo trang web'
        PUBLIC_ATTACHMENT = 'public_attachment', 'File đính kèm công khai'

        # Private Components (Cần check quyền)
        LESSON_MATERIAL = 'lesson_material', 'Tài liệu bài học'
        QUIZ_ATTACHMENT = 'quiz_attachment', 'File trong đề thi'
        SUBMISSION_FILE = 'submission_file', 'Bài nộp của học viên'


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
    component = models.CharField(max_length=100, db_index=True, blank=True, null=True, choices=Component.choices)

    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True, # Cho phép file staging (chưa commit)
        blank=True
    )
    object_id = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    mime_type = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.PositiveIntegerField(default=0)

    sort_order = models.IntegerField(default=0)

    def __str__(self):
        return self.original_filename or self.file.name

    @property
    def url(self):
        """
        Trả về URL cho Frontend dùng.
        """
        if not self.file:
            return None
            
        # NẾU LÀ PUBLIC COMPONENT (Avatar, Thumbnail)
        if self.component in [Component.USER_AVATAR, Component.COURSE_THUMBNAIL, Component.SITE_LOGO]:
            # Trả về URL trực tiếp, loại bỏ Query Params (Signature) (VD: https://bucket.s3.amazonaws.com/media/avatar/xyz.jpg)
            # YÊU CẦU: Folder trên S3 chứa các file này phải được set Policy Public Read.
            return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{self.file.name}"

        from media.services.cloud_service import generate_cloudfront_signed_url
        # NẾU LÀ PRIVATE (Bài giảng)
        # Trả về URL "Gác cổng" API của bạn để check quyền
        return generate_cloudfront_signed_url(self.file.name)
    
#     