import uuid
from datetime import datetime
from django.db.models import Q, Case, When, IntegerField, Count
from typing import Optional, List, Dict, Any

from custom_account.domains.user_domain import UserDomain
from core.exceptions import DomainValidationError, InvalidOperation, ModuleNotFoundError
from content.domains.module_domain import ModuleDomain
from content.domains.subject_domain import SubjectDomain
from content.domains.category_domain import CategoryDomain
from content.domains.tag_domain import TagDomain
from content.types import CourseFetchStrategy
from content.models import ContentBlock
from media.services.cloud_service import get_signed_url_by_id



class CourseDomain:
    """
    Aggregate root: Course gồm nhiều Module; Module có Lesson; Lesson có LessonVersion.
    Business rules (encoded here):
    - Course.slug format validated here (but uniqueness must be checked by app layer).
    - Publish rules (default policy): course can be published only when:
        * it has >=1 module
        * and there exists at least one published lesson version in the course
      (You can call `publish()` with stricter flag `require_all_lessons_published=True`).
    - Course.owner can be None (system content).
    """

    def __init__(self,
                 title: str,
                 id: Optional[str] = None,
                
                 published: bool = False,
                 grade: Optional[str] = None,
                 price: float = 0,               
                 currency: str = 'VND',
                 is_free: bool = True,

                 slug: Optional[str] = None,
                 description: Optional[str] = None,
                 short_description: Optional[str] = None,
                 thumbnail_url: Optional[str] = None,
                 
                 owner_id: Optional[str] = None,
                 owner_name: Optional[str] = None,
                 subject: Dict = None,
    
                 categories: List[Dict] = None,  # List object: [{'id': 1, 'name': 'A'}]
                 tags: List[str] = None,
                 
                 enrollment_count: int = 0,      
                 avg_rating: float = 0.0,
                 module_count: int = 0,
                 stats: Optional[Dict[str, int]] = None, # (số video, số quiz)

                 created_at: Optional[datetime] = None, 
                 updated_at: Optional[datetime] = None, 
                 published_at: Optional[datetime] = None):
                 
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.slug = slug
        self.description = description
        self.short_description = short_description

        self.published = published
        self.grade = grade
        self.price = price
        self.currency = currency
        self.is_free = is_free

        self.thumbnail_url = thumbnail_url

        self.owner_id = owner_id
        self.owner_name = owner_name
        self.subject = subject

        self.categories = categories or []
        self.tags = tags or []

        self.enrollment_count = enrollment_count
        self.avg_rating = avg_rating
        self.module_count = module_count
        self.stats = stats or {}
        
        self.created_at = created_at
        self.updated_at = updated_at
        self.published_at = published_at 

        self.modules: List[ModuleDomain] = []
        self.validate()

    def validate(self):
        if not self.title or not self.title.strip():
            raise DomainValidationError("Course.title is required.")
        if self.slug and (" " in self.slug or len(self.slug) < 2):
            raise DomainValidationError("Course.slug must be at least 2 chars and have no spaces.")
        # grade length check
        if self.grade and len(str(self.grade)) > 16:
            raise DomainValidationError("Course.grade too long.")

    # # ---- Module manipulation (aggregate boundary) ----
    # def add_module(self, title: str, position: Optional[int] = None) -> "ModuleDomain":
    #     if not title or not title.strip():
    #         raise DomainValidationError("Module title required.")
    #     position = position if position is not None else len(self.modules)
    #     if position < 0 or position > len(self.modules):
    #         raise DomainValidationError("position out of range.")
    #     # shift positions of existing modules if needed
    #     for m in self.modules:
    #         if m.position >= position:
    #             m.position += 1
    #     module = ModuleDomain(course_id=self.id, title=title, position=position)
    #     self.modules.append(module)
    #     # normalize to keep consistent ordering
    #     self._normalize_modules_positions()
    #     return module

    # def remove_module(self, module_id: str):
    #     found = None
    #     for m in self.modules:
    #         if m.id == module_id:
    #             found = m
    #             break
    #     if not found:
    #         raise ModuleNotFoundError("Module not found in course.")
    #     self.modules.remove(found)
    #     self._normalize_modules_positions()

    # def move_module(self, module_id: str, new_position: int):
    #     if new_position < 0 or new_position >= len(self.modules):
    #         raise DomainValidationError("new_position out of range.")
    #     module = next((m for m in self.modules if m.id == module_id), None)
    #     if not module:
    #         raise ModuleNotFoundError("Module not found.")
    #     self.modules.remove(module)
    #     self.modules.insert(new_position, module)
    #     self._normalize_modules_positions()

    # def _normalize_modules_positions(self):
    #     # keep positions sequential 0..n-1
    #     self.modules.sort(key=lambda m: m.position)
    #     for idx, m in enumerate(self.modules):
    #         m.position = idx

    # def get_module(self, module_id: str) -> "ModuleDomain":
    #     m = next((m for m in self.modules if m.id == module_id), None)
    #     if not m:
    #         raise ModuleNotFoundError("Module not found.")
    #     return m

    # def list_module_summaries(self) -> List[Dict[str, Any]]:
    #     return [m.to_dict(summary=True) for m in self.modules]

    # # ---- Publishing rules ----
    # def can_publish(self, require_all_lessons_published: bool = False) -> Tuple[bool, str]:
    #     # Rule 1: must have at least one module
    #     if not self.modules:
    #         return False, "Course must contain at least one module."
    #     # Rule 2: must have at least one lesson with published version
    #     any_published = False
    #     for m in self.modules:
    #         for l in m.lessons:
    #             if l.has_published_version():
    #                 any_published = True
    #                 break
    #         if any_published:
    #             break
    #     if not any_published:
    #         return False, "Course must contain at least one lesson with a published version."
    #     # Rule 3 (optional strict): every lesson must have a published version
    #     if require_all_lessons_published:
    #         for m in self.modules:
    #             for l in m.lessons:
    #                 if not l.has_published_version():
    #                     return False, f"Lesson '{l.title}' must have a published version."
    #     return True, "OK"

    # def publish(self, require_all_lessons_published: bool = False):
    #     ok, reason = self.can_publish(require_all_lessons_published=require_all_lessons_published)
    #     if not ok:
    #         raise InvalidOperation(f"Cannot publish course: {reason}")
    #     self.published = True
    #     self.published_at = datetime.datetime.now()

    # def unpublish(self):
    #     # no complex rule: unpublish allowed anytime
    #     self.published = False
    #     self.published_at = None

    # ---- Serialization helpers ----
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "thumbnail_url": self.thumbnail_url,

            "price": self.price,
            "currency": self.currency,
            "is_free": self.price == 0,

            "published": self.published,
            "grade": self.grade,

            "categories": self.categories,
            "tags": self.tags,

            "metrics": {
                "enrollment_count": self.enrollment_count,
                "avg_rating": self.avg_rating,
                "module_count": self.module_count,
                **self.stats # Merge thêm stats chi tiết (video count, quiz count) nếu có
            },
            
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,

            "modules": [m.to_dict() for m in self.modules],
        }
    
    # =========================================================================
    # 1. HELPERS (Clean Logic)
    # =========================================================================

    @staticmethod
    def _resolve_thumbnail(model):
        """Lấy URL ảnh bìa. Ưu tiên model.thumbnail"""
        if hasattr(model, 'thumbnail') and model.thumbnail:
            try:
                # Nếu dùng S3 Public Storage, property .url sẽ trả về link public
                return model.thumbnail.url
            except Exception:
                pass
        return None
    
    @staticmethod
    def _truncate_text(text: str, limit: int = 150) -> str:
        if not text:
            return ""
        if len(text) <= limit:
            return text
        
        # Cắt đúng giới hạn
        truncated = text[:limit]
        
        # (Tùy chọn) Cố gắng lùi lại tìm khoảng trắng để không cắt giữa từ
        # Nếu không tìm thấy khoảng trắng thì chấp nhận cắt thô
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
            
        return f"{truncated}..."

    @staticmethod
    def _extract_base_data(model) -> dict: 
        """
        Map các trường cơ bản và các trường đã ANNOTATE từ Service.
        """
        # 1. Subject là ForeignKey (1-1), không phải list.
        # 2. Cần check if model.subject tồn tại trước khi chấm (.)
        # 3. Model Subject thường dùng field 'title', không phải 'name' (check lại model của bạn)
        subject_obj = None
        if model.subject:
            subject_obj = {
                "id": model.subject.id,
                "title": model.subject.title, # Lưu ý: Model Subject thường là title
                "slug": model.subject.slug
            }

        # --- SỬA 1: Lấy full object cho Category (thêm slug) ---
        category_objs = [
            {"id": c.id, "name": c.name, "slug": c.slug} for c in model.categories.all()
        ]

        # --- SỬA 2: Lấy full object cho Tag (thay vì list string) ---
        # Frontend cần slug để tạo link tag
        tag_objs = [
            {"id": t.id, "name": t.name, "slug": t.slug} for t in model.tags.all()
        ]

        stats = {
            "total_modules": getattr(model, 'modules_count', 0),
            "total_lessons": getattr(model, 'total_lessons', 0),
            "total_videos": getattr(model, 'total_videos', 0),
            "total_quizzes": getattr(model, 'total_quizzes', 0),
            # "students_count": getattr(model, 'students_count', 0),
            "total_seconds": getattr(model, 'total_seconds', 0),                    # NEW: Để frontend filter
            "duration_display": CourseDomain._format_duration(getattr(model, 'total_seconds', 0)),
        }

        return {
            "id": str(model.id),
            "title": model.title,
            "slug": model.slug,
            "description": model.description,
            "short_description": CourseDomain._truncate_text(model.description),

            "price": str(model.price) if model.price is not None else "0",
            "currency": model.currency,
            "is_free": model.is_free,
            "published": model.published,
            "grade": model.grade,

            "owner_id": model.owner_id,
            "owner_name": model.owner.username if model.owner else None,
            "subject": subject_obj,
            
            "categories": category_objs,
            "tags": tag_objs,

            "thumbnail_url": CourseDomain._resolve_thumbnail(model),
            
            "stats": stats,

            "updated_at": model.updated_at,
        }

    @staticmethod
    def _load_structure(domain, model):
        """
        Helper: Load cây Modules -> Lessons.
        lite_mode = True  -> Chỉ lấy khung xương (Syllabus), KHÔNG lấy payload/content.
        lite_mode = False -> Lấy full (Dùng cho người đã mua, hoặc xuất Excel).
        """
        if hasattr(model, 'modules'):
            # Sort module bằng Python (tận dụng prefetch)
            sorted_modules = sorted(model.modules.all(), key=lambda m: m.position)
            for module in sorted_modules:
                domain.modules.append(
                    ModuleDomain.from_model(module)
                )

    @staticmethod
    def _format_duration(seconds: int) -> str:
        if not seconds:
            return "0m"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    # =========================================================================
    # 2. FACTORY CENTER (Dispatcher)
    # =========================================================================
    @classmethod
    def factory(cls, model, strategy: CourseFetchStrategy):
        """
        Single Entry Point: Điều hướng việc tạo Domain Object theo Strategy.
        """
        # 1. Base Data (Metadata, Image, Tags)
        data = cls._extract_base_data(model)

        if strategy == CourseFetchStrategy.BASIC:
            # Case 0: Basic (Chỉ metadata cơ bản)
            return cls(**data)

        # 2. Strategy Mapping
        elif strategy == CourseFetchStrategy.CATALOG_LIST:
            # Case 1: List đơn giản
            return cls(**data)
        
        elif strategy == CourseFetchStrategy.STRUCTURE:
            # Case 3: Preview (Stats chi tiết + Syllabus rút gọn)
            domain = cls(**data)
            cls._load_structure(domain, model) 
            return domain
        
        elif strategy == CourseFetchStrategy.INSTRUCTOR_DASHBOARD:
            data.update({
                "created_at": model.created_at,
                "published_at": model.published_at,
                "stats": {
                    "total_modules": getattr(model, 'modules_count', 0),
                    "total_lessons": getattr(model, 'total_lessons', 0),
                    "total_videos": getattr(model, 'total_videos', 0),
                    "total_quizzes": getattr(model, 'total_quizzes', 0),
                    "students_count": getattr(model, 'students_count', 0),
                    "total_seconds": getattr(model, 'total_seconds', 0),                    # NEW: Để frontend filter
                    "duration_display": CourseDomain._format_duration(getattr(model, 'total_seconds', 0)),
                }
            })
            return cls(**data)

        elif strategy == CourseFetchStrategy.INSTRUCTOR_DETAIL:
            data.update({
                "created_at": model.created_at,
                "published_at": model.published_at,
                "stats": {
                    "total_modules": getattr(model, 'modules_count', 0),
                    "total_lessons": getattr(model, 'total_lessons', 0),
                    "total_videos": getattr(model, 'total_videos', 0),
                    "total_quizzes": getattr(model, 'total_quizzes', 0),
                    "students_count": getattr(model, 'students_count', 0),
                    "total_seconds": getattr(model, 'total_seconds', 0),                    # NEW: Để frontend filter
                    "duration_display": CourseDomain._format_duration(getattr(model, 'total_seconds', 0)),
                }
            })
            domain = cls(**data)
            cls._load_structure(domain, model)
            return domain

        elif strategy == CourseFetchStrategy.ADMIN_LIST:
            # Case 2: Admin List (Thêm thông tin hệ thống)
            data.update({
                "created_at": model.created_at,
                "published_at": model.published_at,
                "stats": {
                    "total_modules": getattr(model, 'modules_count', 0),
                    "total_lessons": getattr(model, 'total_lessons', 0),
                    "total_videos": getattr(model, 'total_videos', 0),
                    "total_quizzes": getattr(model, 'total_quizzes', 0),
                    "students_count": getattr(model, 'students_count', 0),
                    "total_seconds": getattr(model, 'total_seconds', 0),                    # NEW: Để frontend filter
                    "duration_display": CourseDomain._format_duration(getattr(model, 'total_seconds', 0)),
                }
            })
            return cls(**data)

        elif strategy == CourseFetchStrategy.ADMIN_DETAIL:
            data.update({
                "created_at": model.created_at,
                "published_at": model.published_at,
                "stats": {
                    "total_modules": getattr(model, 'modules_count', 0),
                    "total_lessons": getattr(model, 'total_lessons', 0),
                    "total_videos": getattr(model, 'total_videos', 0),
                    "total_quizzes": getattr(model, 'total_quizzes', 0),
                    "students_count": getattr(model, 'students_count', 0),
                    "total_seconds": getattr(model, 'total_seconds', 0),                    # NEW: Để frontend filter
                    "duration_display": CourseDomain._format_duration(getattr(model, 'total_seconds', 0)),
                }
            })
            domain = cls(**data)
            cls._load_structure(domain, model)
            return domain
        
        return cls(**data)
    
