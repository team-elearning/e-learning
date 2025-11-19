
from rest_framework import serializers



class BlockHeartbeatSerializer(serializers.Serializer):
    # Validate format UUID
    block_id = serializers.UUIDField(required=True)
    
    # Validate dict, cho phép rỗng
    resume_data = serializers.DictField(required=False, default=dict)
    
    # Validate boolean
    is_completed = serializers.BooleanField(required=False, default=False)
    
    # Validate số nguyên dương (tránh hack gửi số âm để trừ giờ học)
    time_spent_add = serializers.IntegerField(required=False, default=0, min_value=0)
