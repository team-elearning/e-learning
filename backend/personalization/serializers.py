from rest_framework import serializers



class AISyncSerializer(serializers.Serializer):
    force_update = serializers.BooleanField(required=False, default=False)


class AIRecommendationQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=True, min_length=1)
    top_n = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)