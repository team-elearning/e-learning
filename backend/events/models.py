import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class PlatformEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    type = models.CharField(
        max_length=32,
        choices=[('quiz', ('Quiz')), ('challenge', ('Challenge')), ('webinar', ('Webinar'))]
    )
    config = models.JSONField(default=dict)  # e.g., {'questions': 15, 'duration': 3600}
    status = models.CharField(
        max_length=32,
        default='upcoming',
        choices=[('upcoming', ('Upcoming')), ('ongoing', ('Ongoing')), ('ended', ('Ended'))]
    )

    class Meta:
        verbose_name = ('Platform Event')
        verbose_name_plural = ('Platform Events')
        ordering = ['start_date']

    def __str__(self):
        return self.name

class EventParticipation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(PlatformEvent, on_delete=models.CASCADE, related_name='participations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_participations')
    joined_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0, validators=[MinValueValidator(0)])
    rank = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    metadata = models.JSONField(default=dict)  # e.g., {'answers': [...]}

    class Meta:
        unique_together = ('event', 'user')
        verbose_name = ('Event Participation')
        verbose_name_plural = ('Event Participations')

    def __str__(self):
        return f"{self.user} in {self.event}"

class Leaderboard(models.Model):
    # Aggregate leaderboard for events.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(PlatformEvent, on_delete=models.CASCADE, related_name='leaderboards')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leaderboard_entries')
    score = models.FloatField(validators=[MinValueValidator(0)])
    rank = models.IntegerField(validators=[MinValueValidator(1)])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('event', 'user')
        verbose_name = ('Leaderboard')
        verbose_name_plural = ('Leaderboards')
        ordering = ['rank']

    def __str__(self):
        return f"Rank {self.rank} for {self.user} in {self.event}"