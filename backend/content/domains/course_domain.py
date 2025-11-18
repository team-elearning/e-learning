import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from custom_account.domains.user_domain import UserDomain
from content.services.exceptions import DomainValidationError, NotFoundError, InvalidOperation
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
                 owner_obj: Optional[Any] = None,
                 subject_obj: Optional[Any] = None,
                 category_objs: Optional[List[Any]] = None,
                 tag_objs: Optional[List[Any]] = None):
        self.id = id or str(uuid.uuid4())

        self.owner = owner_obj 
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
            raise NotFoundError("Module not found in course.")
        self.modules.remove(found)
        self._normalize_modules_positions()

    def move_module(self, module_id: str, new_position: int):
        if new_position < 0 or new_position >= len(self.modules):
            raise DomainValidationError("new_position out of range.")
        module = next((m for m in self.modules if m.id == module_id), None)
        if not module:
            raise NotFoundError("Module not found.")
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
            raise NotFoundError("Module not found.")
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
            "modules": [m.to_dict() for m in self.modules],
        }

    @classmethod
    def from_model(cls, model):
        """
        [CẬP NHẬT] Hàm 'nặng' (full) này dùng cho Detail View.
        Nó sẽ gọi hàm 'nhẹ' trước.
        """
        # Dùng lại hàm overview để lấy tất cả metadata cơ bản
        course_domain = cls.from_model_overview(model)
        
        # Giờ mới load 'children' (phần nặng)
        # Service nào gọi hàm này PHẢI prefetch 'modules__lessons'
        modules_sorted = sorted(model.modules.all(), key=lambda m: m.position)
        for module_model in modules_sorted:
            module_domain = ModuleDomain.from_model(module_model)
            course_domain.modules.append(module_domain)
        
        return course_domain
    
    @classmethod
    def from_model_admin(cls, model):
        """
        [MỚI] Hàm 'Full Detail' dành cho Admin View (GET /admin/courses/<pk>/).
        
        Bao gồm:
        1. Metadata đầy đủ & Relations dạng Object (Tái sử dụng from_model_overview_admin).
        2. Cấu trúc cây nội dung (Modules -> Lessons -> ...).
        """
        # 1. Bước nền: Lấy Metadata + Full Relations (Owner, Subject, Tags...)
        # Chúng ta gọi lại hàm overview vừa viết để không phải copy-paste code
        course_domain = cls.from_model_overview_admin(model)
        
        # 2. Bước nạp nội dung con (Modules)
        # Lưu ý quan trọng: Service gọi hàm này PHẢI prefetch_related('modules__lessons')
        # để đảm bảo hiệu năng.
        
        if hasattr(model, 'modules'):
            # Sắp xếp module theo vị trí (position) để hiển thị đúng thứ tự
            modules_sorted = sorted(model.modules.all(), key=lambda m: m.position)
            
            for module_model in modules_sorted:
                # Convert Module Model -> Module Domain
                # (Giả sử ModuleDomain.from_model đã xử lý việc load lessons bên trong)
                module_domain = ModuleDomain.from_model(module_model)
                course_domain.modules.append(module_domain)
        
        return course_domain
    

    @classmethod
    def from_model_overview(cls, model):
        """
        [MỚI] Hàm "nhẹ" - Chỉ map metadata, KHÔNG load 'children' (modules).
        """
        course_domain = cls(
            id=str(model.id),
            title=model.title,
            
            subject_id=str(model.subject_id) if model.subject_id else None,
            owner_id=model.owner_id if model.owner_id else None,
            
            description=model.description,
            grade=model.grade,
            slug=model.slug,
            published=model.published,
            published_at=model.published_at,
            
            # M2M này OK vì đã prefetch ở service
            category_names=[cat.name for cat in model.categories.all()],
            tag_names=[tag.name for tag in model.tags.all()] 
        )
        
        # Dòng này giờ sẽ rất nhanh VÌ chúng ta sẽ prefetch 'files' ở Bước 3
        first_file = model.files.first() 
        if first_file:
            course_domain.image_url = first_file.url
        
        return course_domain
    

    @classmethod
    def from_model_overview_admin(cls, model):
        """
        Factory Method DÀNH RIÊNG CHO ADMIN.
        Nó map dữ liệu 'giàu' (Full Objects) vào Domain.
        """
        # 1. Convert các quan hệ sang Domain con (hoặc Dict)
        #    Điều này thỏa mãn yêu cầu của Pydantic Admin DTO
        
        # Owner (User)
        owner_domain = None
        if model.owner:
            # Giả sử UserDomain có from_model
            owner_domain = UserDomain.from_model(model.owner) 

        # Subject
        subject_domain = None
        if model.subject:
            # Giả sử SubjectDomain có from_model
            subject_domain = SubjectDomain.from_model(model.subject)

        # Categories & Tags (List of Domains)
        category_domains = [
            CategoryDomain.from_model(cat) for cat in model.categories.all()
        ]
        tag_domains = [
            TagDomain.from_model(tag) for tag in model.tags.all()
        ]

        # 2. Khởi tạo CourseDomain với các object vừa tạo
        course_domain = cls(
            id=str(model.id),
            title=model.title,
            description=model.description,
            grade=model.grade,
            slug=model.slug,
            published=model.published,
            published_at=model.published_at,
            
            # Các ID vẫn giữ để tương thích ngược
            owner_id=model.owner_id,
            subject_id=str(model.subject_id) if model.subject_id else None,
            
            # --- TRUYỀN FULL OBJECTS VÀO ĐÂY ---
            owner_obj=owner_domain,
            subject_obj=subject_domain,
            category_objs=category_domains,
            tag_objs=tag_domains,
        )
        
        # Xử lý File ảnh
        first_file = model.files.first()
        if first_file:
            course_domain.image_url = first_file.url
            
        return course_domain