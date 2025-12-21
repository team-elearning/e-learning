from rest_framework import serializers



class ActivityLogItemSerializer(serializers.Serializer):
    action = serializers.CharField(max_length=50, required=True)
    entity_type = serializers.CharField(max_length=50, required=False, allow_null=True)
    entity_id = serializers.CharField(max_length=100, required=False, allow_null=True)
    payload = serializers.DictField(required=False, default=dict)
    session_id = serializers.CharField(max_length=50, required=False, allow_null=True)
    is_critical = serializers.BooleanField(required=False, default=False)


class ActivityBatchSerializer(serializers.Serializer):
    batch = ActivityLogItemSerializer(many=True, required=True, allow_empty=False)


class CourseHealthAnalyzeSerializer(serializers.Serializer):
    """
    Validate body request khi giáo viên bấm nút "Phân tích ngay".
    """
    force_recalculate = serializers.BooleanField(required=False, default=False)