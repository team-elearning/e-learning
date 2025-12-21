from rest_framework import serializers

from quiz.models import QUESTION_TYPES



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
    """ 
    Chỉ validate phần body, question_id sẽ lấy từ URL 
    Frontend BẮT BUỘC gửi: { "question_type": "...", "answer_data": {...} }
    """
    question_type = serializers.ChoiceField(choices=QUESTION_TYPES, required=True)
    answer_data = serializers.JSONField(required=True)

    def validate(self, data):
        q_type = data.get('question_type')
        answer = data.get('answer_data')

        if not q_type or not answer:
            return data

        if q_type == 'multiple_choice_single':
            if 'selected_id' not in answer:
                raise serializers.ValidationError({"answer_data": "Thiếu trường 'selected_id'."})
        
        elif q_type == 'multiple_choice_multi':
            if 'selected_ids' not in answer or not isinstance(answer['selected_ids'], list):
                raise serializers.ValidationError({"answer_data": "Thiếu trường 'selected_ids' (phải là list)."})

        elif q_type == 'true_false':
            # Check 1 trong 2 key tùy quy ước
            if 'selected_value' not in answer and 'selected_id' not in answer:
                 raise serializers.ValidationError({"answer_data": "Thiếu trường 'selected_value'."})

        elif q_type in ['short_answer', 'essay', 'fill_in_the_blank']:
            if 'text' not in answer:
                raise serializers.ValidationError({"answer_data": "Thiếu trường 'text'."})
        
        elif q_type == 'matching':
             if 'matches' not in answer:
                raise serializers.ValidationError({"answer_data": "Thiếu trường 'matches'."})

        return data



