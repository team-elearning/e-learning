import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from content.services.exceptions import DomainValidationError
from content.domains.content_block_domain import ContentBlockDomain



class LessonVersionDomain:
    VALID_STATUSES = ("draft", "review", "published", "archived")

    def __init__(self,
                 lesson_id: str,
                 version: int,
                 status: str = "draft",
                 author_id: Optional[int] = None,
                 change_summary: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 id: Optional[str] = None,
                 published_at: Optional[datetime] = None):
        self.id = id or str(uuid.uuid4())
        self.lesson_id = lesson_id
        self.version = int(version)
        self.status = status
        self.author_id = author_id
        self.change_summary = change_summary
        self.created_at = created_at or datetime.now()
        self.published_at = published_at
        self.content_blocks: List["ContentBlockDomain"] = []
        self.validate()

    def validate(self):
        if not self.lesson_id:
            raise DomainValidationError("LessonVersion.lesson_id required.")
        if self.version < 1:
            raise DomainValidationError("LessonVersion.version must be >= 1.")
        if self.status not in self.VALID_STATUSES:
            raise DomainValidationError(f"Invalid LessonVersion.status: {self.status}")

    @property
    def content(self) -> Dict[str, Any]:
        """
        Tự động tạo ra bản sao (cache) JSON 'content' 
        từ danh sách 'content_blocks'.
        """
        return {
            "content_blocks": [block.to_dict() for block in self.content_blocks]
        }

    def add_content_block(self, block: "ContentBlockDomain"):
        from content.domains.content_block_domain import ContentBlockDomain
        if not isinstance(block, ContentBlockDomain):
            raise DomainValidationError("add_content_block expects ContentBlockDomain.")
        self.content_blocks.append(block)
        self._normalize_content_positions()

    def _normalize_content_positions(self):
        self.content_blocks.sort(key=lambda b: b.position)
        for idx, b in enumerate(self.content_blocks):
            b.position = idx

    def to_dict(self):
        return {
            "id": self.id,
            "lesson_id": self.lesson_id,
            "version": self.version,
            "status": self.status,
            "author_id": self.author_id,
            "content": self.content,
            "change_summary": self.change_summary,
            "created_at": self.created_at,
            "published_at": self.published_at,
            "content_blocks": [b.to_dict() for b in self.content_blocks]
        }

    @classmethod
    def from_model(cls, model):
        lv = cls(lesson_id=str(model.lesson.id) if getattr(model,'lesson',None) else str(getattr(model,'lesson_id',None) or ""),
                 version=model.version, status=model.status, author_id=(model.author.id if getattr(model,'author',None) else None),
                 change_summary=getattr(model,'change_summary', None),
                 created_at=getattr(model,'created_at', None), id=str(model.id), published_at=getattr(model,'published_at',None))
        
        if hasattr(model, "content_blocks_prefetched") and model.content_blocks_prefetched:
            for cb_m in model.content_blocks_prefetched:
                lv.content_blocks.append(ContentBlockDomain.from_model(cb_m))
        elif hasattr(model, 'content_blocks'):
            for cb_m in model.content_blocks.all():
                lv.content_blocks.append(ContentBlockDomain.from_model(cb_m))
        
        return lv