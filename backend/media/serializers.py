from rest_framework import serializers

from media.models import Component
from media.models import UploadedFile, FileStatus



class FileUploadInputSerializer(serializers.Serializer):
    """
    DRF Serializer: Chỉ chịu trách nhiệm validate input.
    """
    file = serializers.FileField(required=True)
    component = serializers.ChoiceField(
        choices=Component.choices, 
        required=True,
        error_messages={'invalid_choice': 'Component không hợp lệ. Các giá trị cho phép: {choices}.'}
    )
    content_type_str = serializers.CharField(required=False, max_length=100) 
    object_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        """
        Validate chéo: Nếu gửi object_id thì bắt buộc phải có content_type_str
        """
        object_id = attrs.get('object_id')
        content_type_str = attrs.get('content_type_str')

        if object_id and not content_type_str:
            raise serializers.ValidationError("Nếu gửi object_id, bạn phải gửi kèm content_type_str (VD: 'course.Course').")
        
        return attrs


class FileUpdateInputSerializer(serializers.Serializer):
    # Phải khớp với Pydantic DTO
    component = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=FileStatus.choices, required=False)