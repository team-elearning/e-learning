from typing import Optional, Any
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from custom_account.models import UserModel
from media.models import UploadedFile  


User = get_user_model()

class FileDomain:
    """
    Domain object cho một UploadedFile.
    """
    def __init__(self, 
                 file: Any, 
                 original_filename: str, 
                 uploaded_by: UserModel, 
                 content_type: Optional[ContentType] = None,
                 status: Optional[str] = None, 
                 object_id: Optional[int] = None, 
                 component: Optional[str] = None, 
                 id: Optional[int] = None, 
                 uploaded_at: Optional[Any] = None,
                 url: Optional[str] = None):
        
        self.id = id
        self.file = file
        self.original_filename = original_filename
        self.uploaded_by = uploaded_by  
        self.uploaded_at = uploaded_at
        self.component = component
        
        # Context
        self.content_type = content_type  
        self.object_id = object_id

        self.status = status
        self.url = url

    @classmethod
    def from_model(cls, model: UploadedFile) -> 'FileDomain':
        """Tạo một domain object từ một model instance."""
        return cls(
            id=model.id,
            file=model.file,
            original_filename=model.original_filename,
            uploaded_by=model.uploaded_by,
            uploaded_at=model.uploaded_at,
            component=model.component,
            content_type=model.content_type,
            object_id=model.object_id,
            status=model.status,
            url=model.url
        )

    def to_model(self) -> UploadedFile:
        """
        Chuyển domain object thành một model instance (chưa save).
        """

        return UploadedFile(
            file=self.file,
            original_filename=self.original_filename,
            uploaded_by=self.uploaded_by,
            component=self.component,
            content_type=self.content_type,
            object_id=self.object_id,
            # id và uploaded_at sẽ được tự động gán khi save

            status=self.status
        )
