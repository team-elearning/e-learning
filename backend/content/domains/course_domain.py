import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from django.db.models import Q, Case, When, IntegerField

from custom_account.domains.user_domain import UserDomain
from core.exceptions import DomainValidationError, InvalidOperation, ModuleNotFoundError
from content.domains.module_domain import ModuleDomain
from content.domains.subject_domain import SubjectDomain
from content.domains.category_domain import CategoryDomain
from content.domains.tag_domain import TagDomain



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
                 subject_id: Optional[str] = None,
                 description: Optional[str] = None,
                 grade: Optional[str] = None,
                 owner_id: Optional[int] = None,
                 slug: Optional[str] = None,
                 id: Optional[str] = None,
                 published: bool = False,
                 published_at: Optional[datetime] = None, 
                 category_names: List[str] = None,
                 tag_names: List[str] = None,
                 image_url: Optional[str] = None,
                 module_count: int = 0,
                 subject_obj: Optional[Any] = None,
                 category_objs: Optional[List[Any]] = None,
                 tag_objs: Optional[List[Any]] = None):
        self.id = id or str(uuid.uuid4())

        self.subject = subject_obj
        self.categories = category_objs if category_objs is not None else (category_names or [])
        self.tags = tag_objs if tag_objs is not None else (tag_names or [])

        self.title = title
        self.subject_id = subject_id
        self.description = description
        self.grade = grade
        self.owner_id = owner_id
        self.slug = slug
        self.published = published
        self.published_at = published_at 
        self.category_names = category_names or []
        self.tag_names = tag_names or []
        self.modules: List[ModuleDomain] = []
        self.image_url = image_url
        self.module_count = module_count
        self.validate()

    def validate(self):
        if not self.title or not self.title.strip():
            raise DomainValidationError("Course.title is required.")
        if self.slug and (" " in self.slug or len(self.slug) < 2):
            raise DomainValidationError("Course.slug must be at least 2 chars and have no spaces.")
        # grade length check
        if self.grade and len(str(self.grade)) > 16:
            raise DomainValidationError("Course.grade too long.")

    # ---- Module manipulation (aggregate boundary) ----
    def add_module(self, title: str, position: Optional[int] = None) -> "ModuleDomain":
        if not title or not title.strip():
            raise DomainValidationError("Module title required.")
        position = position if position is not None else len(self.modules)
        if position < 0 or position > len(self.modules):
            raise DomainValidationError("position out of range.")
        # shift positions of existing modules if needed
        for m in self.modules:
            if m.position >= position:
                m.position += 1
        module = ModuleDomain(course_id=self.id, title=title, position=position)
        self.modules.append(module)
        # normalize to keep consistent ordering
        self._normalize_modules_positions()
        return module

    def remove_module(self, module_id: str):
        found = None
        for m in self.modules:
            if m.id == module_id:
                found = m
                break
        if not found:
            raise ModuleNotFoundError("Module not found in course.")
        self.modules.remove(found)
        self._normalize_modules_positions()

    def move_module(self, module_id: str, new_position: int):
        if new_position < 0 or new_position >= len(self.modules):
            raise DomainValidationError("new_position out of range.")
        module = next((m for m in self.modules if m.id == module_id), None)
        if not module:
            raise ModuleNotFoundError("Module not found.")
        self.modules.remove(module)
        self.modules.insert(new_position, module)
        self._normalize_modules_positions()

    def _normalize_modules_positions(self):
        # keep positions sequential 0..n-1
        self.modules.sort(key=lambda m: m.position)
        for idx, m in enumerate(self.modules):
            m.position = idx

    def get_module(self, module_id: str) -> "ModuleDomain":
        m = next((m for m in self.modules if m.id == module_id), None)
        if not m:
            raise ModuleNotFoundError("Module not found.")
        return m

    def list_module_summaries(self) -> List[Dict[str, Any]]:
        return [m.to_dict(summary=True) for m in self.modules]

    # ---- Publishing rules ----
    def can_publish(self, require_all_lessons_published: bool = False) -> Tuple[bool, str]:
        # Rule 1: must have at least one module
        if not self.modules:
            return False, "Course must contain at least one module."
        # Rule 2: must have at least one lesson with published version
        any_published = False
        for m in self.modules:
            for l in m.lessons:
                if l.has_published_version():
                    any_published = True
                    break
            if any_published:
                break
        if not any_published:
            return False, "Course must contain at least one lesson with a published version."
        # Rule 3 (optional strict): every lesson must have a published version
        if require_all_lessons_published:
            for m in self.modules:
                for l in m.lessons:
                    if not l.has_published_version():
                        return False, f"Lesson '{l.title}' must have a published version."
        return True, "OK"

    def publish(self, require_all_lessons_published: bool = False):
        ok, reason = self.can_publish(require_all_lessons_published=require_all_lessons_published)
        if not ok:
            raise InvalidOperation(f"Cannot publish course: {reason}")
        self.published = True
        self.published_at = datetime.datetime.now()

    def unpublish(self):
        # no complex rule: unpublish allowed anytime
        self.published = False
        self.published_at = None

    # ---- Serialization helpers ----
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "subject_id": self.subject_id,
            "description": self.description,
            "grade": self.grade,
            "owner_id": self.owner_id,
            "slug": self.slug,
            "published": self.published,
            "published_at": self.published_at,
            "categories": self.categories,
            "tags": self.tags,
            "image_url": self.image_url,
            "module_count": self.module_count,
            "modules": [m.to_dict() for m in self.modules],
        }
    
    @staticmethod
    def _map_base_attributes(model) -> dict:
        """
        Trích xuất các trường Primitive (Cơ bản) dùng chung cho mọi Strategy.
        """
        image_url = None

        # Logic lấy ảnh bìa
        # 1. Định nghĩa điều kiện là Ảnh (Cách 2 - Check extension)
        img_exts = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        q_is_image = Q()
        for ext in img_exts:
            q_is_image |= Q(file__iendswith=ext)

        # 2. Query kết hợp (Cách 3 - Component)
        # Logic: Lấy ra tất cả file thuộc course này
        # Sắp xếp ưu tiên:
        #   - Component là 'course_thumbnail' lên đầu (Priority cao nhất)
        #   - Sau đó đến sort_order (User sắp xếp)
        #   - Sau đó đến created_at
        
        files_qs = model.files.filter(
            # Chỉ lấy những file LÀ ẢNH (để tránh lấy nhầm PDF làm thumbnail)
            q_is_image
        ).annotate(
            # Tạo field tạm 'is_thumbnail' để sort
            is_explicit_thumbnail=Case(
                When(component='course_thumbnail', then=1), # Là thumbnail -> 1
                default=0,                                  # Không phải -> 0
                output_field=IntegerField(),
            )
        ).order_by(
            '-is_explicit_thumbnail', # Số 1 lên trước (DESC)
            'sort_order',             # Thứ tự user chỉnh
            'uploaded_at'              # Mới nhất
        )

        # Lấy file đầu tiên sau khi đã sort theo ưu tiên
        first_valid_image = files_qs.first()

        if first_valid_image:
            image_url = first_valid_image.url

        # --- [UPDATE 4] Logic lấy module_count ---
        # Ưu tiên lấy từ annotate (tối ưu hiệu năng) nếu có,
        # nếu không thì mới query count()
        count = getattr(model, 'module_count', None)
        if count is None:
             # Fallback: Đếm trực tiếp (lưu ý N+1 query nếu list nhiều course)
            count = model.modules.count() if hasattr(model, 'modules') else 0

        return {
            "id": str(model.id),
            "title": model.title,
            "slug": model.slug,
            "description": model.description,
            "grade": model.grade,
            "published": model.published,
            "published_at": model.published_at,
            "owner_id": model.owner__id,
            "subject_id": str(model.subject_id) if model.subject_id else None,
            "image_url": image_url,
            "module_count": count,
        }
    
    @staticmethod
    def _load_modules(course_domain, model):
        """
        Helper để load Modules & Lessons vào domain.
        """
        if hasattr(model, 'modules'):
            # Sort modules
            modules_sorted = sorted(model.modules.all(), key=lambda m: m.position)
            for module_model in modules_sorted:
                # Giả định ModuleDomain.from_model đã xử lý lessons
                course_domain.modules.append(ModuleDomain.from_model(module_model))


    @classmethod
    def from_model_overview(cls, model):
        """
        [STRATEGY: OVERVIEW]
        Chỉ metadata + Tags/Categories dạng String.
        """
        data = cls._map_base_attributes(model)

        data["category_names"] = [cat.name for cat in model.categories.all()]
        data["tag_names"] = [tag.name for tag in model.tags.all()]

        categories = list(model.categories.all())
        tags = list(model.tags.all())

        # Truyền vào key _objs để __init__ nhận diện
        data["category_objs"] = categories
        data["tag_objs"] = tags
        
        return cls(**data)
    
    @classmethod
    def from_model(cls, model):
        """
        [STRATEGY: FULL_STRUCTURE]
        Overview + Cấu trúc bài học (Modules -> Lessons).
        Dùng cho màn hình Learning hoặc Instructor Edit.
        """
        # 1. Tái sử dụng Overview để lấy metadata & string tags
        domain = cls.from_model_overview(model)
        
        # 2. Load thêm Modules
        cls._load_modules(domain, model)
        
        return domain

    @classmethod
    def from_model_admin(cls, model):
        """
        [STRATEGY: ADMIN_DETAIL]
        Metadata + Full Objects (User, Subject, Tags) + Modules.
        Dùng cho Admin Dashboard.
        """
        # 1. Lấy khung sườn
        data = cls._map_base_attributes(model)

        # 2. Đắp thịt (Dạng Full Object "Giàu")       
        if model.subject:
            data["subject_obj"] = SubjectDomain.from_model(model.subject)

        data["category_objs"] = [CategoryDomain.from_model(c) for c in model.categories.all()]
        data["tag_objs"] = [TagDomain.from_model(t) for t in model.tags.all()]

        # 3. Tạo object
        domain = cls(**data)

        # 4. Load thêm Modules (Admin cũng cần xem cấu trúc)
        cls._load_modules(domain, model)

        return domain
