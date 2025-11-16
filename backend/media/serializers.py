from rest_framework import serializers
from media.models import UploadedFile, FileStatus

class FileUploadInputSerializer(serializers.Serializer):
    """
    DRF Serializer: Chỉ chịu trách nhiệm validate input.
    """
    file = serializers.FileField(required=True)
    content_type_str = serializers.CharField(required=False, max_length=100) 
    object_id = serializers.IntegerField(required=False)
    component = serializers.CharField(required=True, max_length=100, allow_blank=True)

class FileUpdateInputSerializer(serializers.Serializer):
    # Phải khớp với Pydantic DTO
    component = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=FileStatus.choices, required=False)