import uuid
from django.db import models
from django.conf import settings

from custom_account.models import UserModel



# # Create your models here.
# class Badge(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=255, unique=True)
#     description = models.TextField()
#     icon_url = models.TextField(blank=True, null=True)
#     criteria = models.JSONField(default=dict)  # e.g., {'complete_lessons': 10, 'min_score': 80}

#     class Meta:
#         verbose_name = ('Badge')
#         verbose_name_plural = ('Badges')

#     def __str__(self):
#         return self.name


# class UserBadge(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
#     badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
#     awarded_at = models.DateTimeField(auto_now_add=True)
#     metadata = models.JSONField(default=dict)  # e.g., {'reason': 'Completed course'}

#     class Meta:
#         unique_together = ('user', 'badge')
#         verbose_name = ('User Badge')
#         verbose_name_plural = ('User Badges')

#     def __str__(self):
#         return f"{self.badge} awarded to {self.user}"


# class Reward(models.Model):
#     # e.g., stars, points.
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rewards')
#     type = models.CharField(max_length=32, choices=[('star', ('Star')), ('point', ('Point')), ('level_up', ('Level Up'))])
#     value = models.IntegerField(validators=[MinValueValidator(1)])
#     awarded_at = models.DateTimeField(auto_now_add=True)
#     source = models.CharField(max_length=128)  # e.g., 'lesson_complete'

#     class Meta:
#         verbose_name = ('Reward')
#         verbose_name_plural = ('Rewards')
#         ordering = ['-awarded_at']

#     def __str__(self):
#         return f"{self.value} {self.type} to {self.user}"


class UserCertificate(models.Model):
    """
    Lưu trữ chứng chỉ đã cấp cho user.
    Chỉ tạo ra khi CourseProgress.percent_completed = 100% HOẶC Pass Final Exam.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Quan hệ
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey("content.Course", on_delete=models.CASCADE, related_name='certificates')
    enrollment = models.ForeignKey("content.Enrollment", on_delete=models.CASCADE) # Link để truy xuất ngày bắt đầu/kết thúc

    # Định danh chứng chỉ (Để nhà tuyển dụng verify)
    # Ví dụ: CERT-2025-ABCD-1234
    certificate_code = models.CharField(max_length=50, unique=True, db_index=True)
    
    # File PDF (Lưu đường dẫn file đã generate)
    file = models.FileField(upload_to='certificates/%Y/%m/', null=True, blank=True)
    
    # Snapshot dữ liệu tại thời điểm cấp (đề phòng user đổi tên sau này)
    issued_to_name = models.CharField(max_length=255, help_text="Tên hiển thị trên bằng")
    issued_at = models.DateTimeField(auto_now_add=True)

    # Trạng thái (Phòng trường hợp thu hồi bằng)
    is_valid = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'course') # Mỗi khóa chỉ cấp 1 bằng
        ordering = ['-issued_at']

    def __str__(self):
        return f"Certificate {self.certificate_code} - {self.user.username}"
    

class UserGamification(models.Model):
    user = models.OneToOneField(UserModel, on_delete=models.CASCADE)
    current_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True)
    longest_streak = models.IntegerField(default=0)
    
    # Tính năng Freeze (Bảo băng) - Kiếm tiền từ đây nè :D
    freeze_equipped = models.BooleanField(default=False)