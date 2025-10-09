# ai_personalization/serializers.py

from rest_framework import serializers
from ai_personalization.models import LearningEvent, RecommendationLog

class LearningEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningEvent
        fields = ['id', 'user', 'course', 'lesson', 'timestamp', 'event_type', 'detail', 'session_id']
        read_only_fields = ['id', 'timestamp']

class RecommendationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationLog
        fields = ['id', 'user', 'lesson', 'score', 'reason', 'source', 'shown_at', 'acted_at', 'accepted', 'feedback']
        read_only_fields = ['id', 'shown_at']
