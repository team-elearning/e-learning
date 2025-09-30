import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator



# Create your models here.
class Badge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    icon_url = models.TextField(blank=True, null=True)
    criteria = models.JSONField(default=dict)  # e.g., {'complete_lessons': 10, 'min_score': 80}

    class Meta:
        verbose_name = ('Badge')
        verbose_name_plural = ('Badges')

    def __str__(self):
        return self.name

class UserBadge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    awarded_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)  # e.g., {'reason': 'Completed course'}

    class Meta:
        unique_together = ('user', 'badge')
        verbose_name = ('User Badge')
        verbose_name_plural = ('User Badges')

    def __str__(self):
        return f"{self.badge} awarded to {self.user}"

class Reward(models.Model):
    # e.g., stars, points.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rewards')
    type = models.CharField(max_length=32, choices=[('star', ('Star')), ('point', ('Point')), ('level_up', ('Level Up'))])
    value = models.IntegerField(validators=[MinValueValidator(1)])
    awarded_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=128)  # e.g., 'lesson_complete'

    class Meta:
        verbose_name = ('Reward')
        verbose_name_plural = ('Rewards')
        ordering = ['-awarded_at']

    def __str__(self):
        return f"{self.value} {self.type} to {self.user}"