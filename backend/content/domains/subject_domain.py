import uuid
from typing import Optional, TypedDict

from core.exceptions import DomainValidationError
from content.models import Subject


class SubjectDict(TypedDict):
    id: str
    title: str
    slug: str


class SubjectDomain:
    def __init__(self, title: str, slug: str, id: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.slug = slug
        self.validate()

    def validate(self):
        if not self.title or not self.title.strip():
            raise DomainValidationError("Subject title required.")
        if not self.slug or " " in self.slug:
            raise DomainValidationError("Subject slug required and cannot contain spaces.")

    def to_dict(self):
        return {"id": self.id, "title": self.title, "slug": self.slug}

    @classmethod
    def from_model(cls, model):
        # model expected to have .id, .title, .slug
        return cls(title=model.title, slug=model.slug, id=str(model.id), )
    
    def to_model(self):
        """
        Chuyển SubjectDomain → Django model instance
        Đây chính là method mà drf-writable-nested / serializer đang tìm!
        """
        if hasattr(self, '_model_cache'):
            return self._model_cache
            
        # Nếu đã có id thật → lấy từ DB (update)
        if self.id and self.id != str(uuid.uuid4()):  # không phải id tạm
            try:
                obj = Subject.objects.get(id=self.id)
                obj.title = self.title
                obj.slug = self.slug
            except Subject.DoesNotExist:
                obj = Subject(id=self.id, title=self.title, slug=self.slug)
        else:
            # Tạo mới
            obj = Subject(id=self.id, title=self.title, slug=self.slug)
        
        self._model_cache = obj
        return obj