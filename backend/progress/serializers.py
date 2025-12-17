
from rest_framework import serializers



class BlockHeartbeatSerializer(serializers.Serializer):    
    # Validate dict, cho phép rỗng
    interaction_data = serializers.DictField(required=False, default=dict)
    
    # Validate boolean
    is_completed = serializers.BooleanField(required=False, default=False)
    
    # Validate số nguyên dương (tránh hack gửi số âm để trừ giờ học)
    time_spent_add = serializers.IntegerField(required=False, default=0, min_value=0)


class BlockCompletionInputSerializer(serializers.Serializer):
    block_id = serializers.UUIDField()
    # Có thể gửi kèm lý do hoặc metadata nếu cần (ví dụ: checksum)
    force_complete = serializers.BooleanField(default=False, required=False)


class StartQuizInputSerializer(serializers.Serializer):
    """Validate đầu vào"""
    quiz_id = serializers.UUIDField()


class QuestionAnswerInputSerializer(serializers.Serializer):
    """ Chỉ validate phần body, question_id sẽ lấy từ URL """
    answer_data = serializers.JSONField(required=True)



