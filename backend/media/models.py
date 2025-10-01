import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator



# Create your models here.
class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    type = models.CharField(
        max_length=32,
        choices=[('video', ('Video')), ('image', ('Image')), ('audio', ('Audio')), ('file', ('File'))]
    )
    url = models.TextField()
    mime = models.CharField(max_length=64)
    size = models.BigIntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])  # seconds
    status = models.CharField(
        max_length=32,
        default='ready',
        choices=[('uploading', ('Uploading')), ('processing', ('Processing')), ('ready', ('Ready')), ('failed', ('Failed'))]
    )

    class Meta:
        verbose_name = ('Asset')
        verbose_name_plural = ('Assets')

    def __str__(self):
        return f"{self.type} at {self.url}"