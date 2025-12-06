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
                 subject_id: Optional[str] = None,
                 description: Optional[str] = None,
                 grade: Optional[str] = None,
                 owner_id: Optional[int] = None,
                 owner_name: Optional[str] = None,
                 slug: Optional[str] = None,
                 id: Optional[str] = None,
                 published: bool = False,
                 published_at: Optional[datetime] = None, 
                 category_names: List[str] = None,
                 tag_names: List[str] = None,
                 subject_name: Optional[str] = None,
                 image_url: Optional[str] = None,
                 image_id: Optional[str] = None,
                 module_count: int = 0,
                 subject_obj: Optional[Any] = None,
                 category_objs: Optional[List[Any]] = None,
                 tag_objs: Optional[List[Any]] = None,
                 created_at: Optional[datetime] = None, 
                 updated_at: Optional[datetime] = None, 
                 stats: Optional[Dict[str, int]] = None): # (số video, số quiz)
        self.id = id or str(uuid.uuid4())

        self.subject = subject_obj
        self.categories = category_objs if category_objs is not None else (category_names or [])
        self.tags = tag_objs if tag_objs is not None else (tag_names or [])

        self.title = title
        self.subject_id = subject_id
        self.description = description
        self.grade = grade
        self.owner_id = owner_id
        self.owner_name = owner_name
        self.slug = slug
        self.published = published
        self.published_at = published_at 
        self.category_names = category_names or []
        self.tag_names = tag_names or []
        self.subject_name = subject_name
        self.modules: List[ModuleDomain] = []
        self.image_url = image_url
        self.image_id = image_id
        self.module_count = module_count
        self.created_at = created_at
        self.updated_at = updated_at
        self.stats = stats or {}
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
    
    # =========================================================================
    # 1. HELPERS (Clean Logic)
    # =========================================================================

    @staticmethod
    def _resolve_course_image(model):
        """Helper: Logic phức tạp để chọn ảnh đại diện."""
        # Logic: Lấy ảnh được mark là 'course_thumbnail' hoặc ảnh đầu tiên
        # Giả định Service đã prefetch files là ảnh rồi.
        
        files = list(model.files.all()) # Đã cache nhờ prefetch
        if not files:
            return None, None

        # Sort in Python (nhanh hơn query lại DB vì số lượng file ít)
        # Ưu tiên: component='course_thumbnail' -> sort_order -> created_at
        def sort_key(f):
            is_thumb = 1 if f.component == 'course_thumbnail' else 0
            return (-is_thumb, f.sort_order, -f.uploaded_at.timestamp())
        
        files.sort(key=sort_key)
        best_file = files[0]
        
        # 3. THAY ĐỔI Ở ĐÂY: Gọi hàm lấy Signed URL trực tiếp
        # Ảnh bìa public hoặc cache lâu (24h)
        url = get_signed_url_by_id(str(best_file.id), expire_minutes=1440)

        return url, str(best_file.id)

    @staticmethod
    def _extract_base_data(model) -> dict:
        """Helper: Lấy metadata và xử lý logic ảnh."""
        image_url, image_id = CourseDomain._resolve_course_image(model)
        
        # Ưu tiên lấy count từ annotate (Service)
        module_count = getattr(model, 'module_count', None)
        if module_count is None:
            module_count = model.modules.count() if hasattr(model, 'modules') else 0

        return {
            "id": str(model.id),
            "title": model.title,
            "slug": model.slug,
            "description": model.description,
            "grade": model.grade,
            "owner_id": model.owner_id,
            "owner_name": model.owner.username if model.owner else None,
            "subject_name": model.subject.title if model.subject else None,
            "category_names": [c.name for c in model.categories.all()],
            "tag_names": [t.name for t in model.tags.all()],
            "image_url": image_url,
            "image_id": image_id,
            "module_count": module_count,
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
    def _calculate_content_stats(model):
        """
        Helper: Tính thống kê (Video, Quiz, Duration).
        CHÚ Ý: Chỉ dùng cho Detail View (1 course) vì query nặng.
        """
        
        # Query aggregate trực tiếp từ ContentBlock
        stats = ContentBlock.objects.filter(
            lesson__module__course_id=model.id
        ).aggregate(
            video_count=Count('id', filter=Q(type='video')),
            quiz_count=Count('id', filter=Q(type='quiz')),
        )
        
        # Mock duration logic (vì chưa có field duration thực tế)
        # Nếu có field duration: total_seconds = stats['total_seconds']
        # Moodle thường lưu duration cache ngay trong bảng Course để list view chạy nhanh.
        total_lessons = sum(m.lessons.count() for m in model.modules.all())
        
        return {
            "total_modules": model.modules.count(),
            "total_lessons": total_lessons,
            "total_videos": stats['video_count'] or 0,
            "total_quizzes": stats['quiz_count'] or 0,
            "duration_display": f"{total_lessons * 10} phút" # Mock
        }
    
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

        elif strategy == CourseFetchStrategy.ADMIN_LIST:
            # Case 2: Admin List (Thêm thông tin hệ thống)
            data.update({
                "created_at": model.created_at,
                "updated_at": model.updated_at,
                "student_count": getattr(model, 'student_count', 0)
            })
            return cls(**data)

        elif strategy == CourseFetchStrategy.STRUCTURE:
            # Case 3: Preview (Stats chi tiết + Syllabus rút gọn)
            domain = cls(**data)
            domain.stats = cls._calculate_content_stats(model)
            cls._load_structure(domain, model) 
            return domain

        elif strategy == CourseFetchStrategy.ADMIN_DETAIL:
            # Case 5: Admin Detail (Full + System Info)
            data.update({
                "subject_obj": SubjectDomain.from_model(model.subject) if model.subject else None,
                # "category_objs": ... (Load full objects if needed)
            })
            domain = cls(**data)
            domain.stats = cls._calculate_content_stats(model)
            cls._load_structure(domain, model, lite_mode=False)
            return domain
        
        return cls(**data)
    
    # @staticmethod
    # def _get_course_stats(model):
    #     """
    #     Helper: Tính toán thống kê cho Course.
    #     Dựa trên cấu trúc: Course -> Module -> Lesson -> ContentBlock
    #     """
        
    #     # CÁCH 1: Nếu 'model' là một object đã được query từ DB (Single Instance)
    #     # Chúng ta query ngược từ ContentBlock lên để đếm cho chính xác
        
    #     # Import model bên trong hàm để tránh circular import nếu cần, 
    #     # hoặc giả định model instance đã có quan hệ ngược (reverse relation)
        
    #     # Đếm số modules (Dễ)
    #     total_modules = model.modules.count()
        
    #     # Đếm số lessons thông qua modules
    #     # Lưu ý: cần distinct=True nếu sợ trùng, nhưng quan hệ 1-n thì count thường ok
    #     total_lessons = getattr(model, 'lessons_count', None)
    #     if total_lessons is None:
    #          # Fallback query: đi từ Modules sang Lessons
    #         total_lessons = 0
    #         for m in model.modules.all():
    #             total_lessons += m.lessons.count()
    #         # Hoặc tối ưu hơn: Lesson.objects.filter(module__course=model).count()
        
    #     # Đếm Video và Quiz dựa trên ContentBlock
    #     # Cách tối ưu: Query trực tiếp bảng ContentBlock filter theo course
    #     # Cần import ContentBlock model hoặc dùng related name nếu có.
    #     # Ở đây giả sử ta dùng related names ngược từ Course xuống.
        
    #     # Tuy nhiên, Django reverse relation mặc định không xuyên qua 2 cấp (Course -> Lesson -> Block).
    #     # Nên cách tốt nhất là query từ ContentBlock:
        
    #     from content.models import ContentBlock # Import model thực tế của bạn
        
    #     # Query 1 lần để lấy các stats về content
    #     stats = ContentBlock.objects.filter(
    #         lesson__module__course_id=model.id
    #     ).aggregate(
    #         video_count=Count('id', filter=Q(type='video')),
    #         quiz_count=Count('id', filter=Q(type='quiz')),
    #         # doc_count=Count('id', filter=Q(type__in=['pdf', 'docx'])),
            
    #         # Nếu bạn có trường duration trong payload hoặc field riêng
    #         # total_seconds=Sum('duration') 
    #     )

    #     total_videos = stats['video_count'] or 0
    #     total_quizzes = stats['quiz_count'] or 0
        
    #     # Logic tính thời gian (Mock vì chưa có field duration)
    #     # Giả sử mỗi bài học trung bình 10 phút để demo
    #     total_seconds = total_lessons * 10 * 60 
    #     hours = total_seconds // 3600
    #     minutes = (total_seconds % 3600) // 60
    #     duration_str = f"{hours}h {minutes}m"

    #     return {
    #         "total_modules": total_modules,
    #         "total_lessons": total_lessons,
    #         "total_videos": total_videos,
    #         "total_quizzes": total_quizzes,
    #         "total_duration": duration_str
    #     }
    
    # @staticmethod
    # def _map_base_attributes(model) -> dict:
    #     """
    #     Trích xuất các trường Primitive (Cơ bản) dùng chung cho mọi Strategy.
    #     """
    #     image_url = None
    #     image_id = None

    #     # Logic lấy ảnh bìa
    #     # 1. Định nghĩa điều kiện là Ảnh (Cách 2 - Check extension)
    #     img_exts = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    #     q_is_image = Q()
    #     for ext in img_exts:
    #         q_is_image |= Q(file__iendswith=ext)

    #     # 2. Query kết hợp (Cách 3 - Component)
    #     # Logic: Lấy ra tất cả file thuộc course này
    #     # Sắp xếp ưu tiên:
    #     #   - Component là 'course_thumbnail' lên đầu (Priority cao nhất)
    #     #   - Sau đó đến sort_order (User sắp xếp)
    #     #   - Sau đó đến created_at
        
    #     files_qs = model.files.filter(
    #         # Chỉ lấy những file LÀ ẢNH (để tránh lấy nhầm PDF làm thumbnail)
    #         q_is_image
    #     ).annotate(
    #         # Tạo field tạm 'is_thumbnail' để sort
    #         is_explicit_thumbnail=Case(
    #             When(component='course_thumbnail', then=1), # Là thumbnail -> 1
    #             default=0,                                  # Không phải -> 0
    #             output_field=IntegerField(),
    #         )
    #     ).order_by(
    #         '-is_explicit_thumbnail', # Số 1 lên trước (DESC)
    #         'sort_order',             # Thứ tự user chỉnh
    #         'uploaded_at'              # Mới nhất
    #     )

    #     # Lấy file đầu tiên sau khi đã sort theo ưu tiên
    #     first_valid_image = files_qs.first()

    #     if first_valid_image:
    #         image_url = first_valid_image.url
    #         image_id = str(first_valid_image.id)

    #     # --- [UPDATE 4] Logic lấy module_count ---
    #     # Ưu tiên lấy từ annotate (tối ưu hiệu năng) nếu có,
    #     # nếu không thì mới query count()
    #     count = getattr(model, 'module_count', None)
    #     if count is None:
    #          # Fallback: Đếm trực tiếp (lưu ý N+1 query nếu list nhiều course)
    #         count = model.modules.count() if hasattr(model, 'modules') else 0

    #     return {
    #         "id": str(model.id),
    #         "title": model.title,
    #         "slug": model.slug,
    #         "description": model.description,
    #         "category_names": [cat.name for cat in model.categories.all()],
    #         "tag_names": [tag.name for tag in model.tags.all()],
    #         "subject_name": model.subject.name if model.subject else None,
    #         "grade": model.grade,
    #         # "published": model.published,
    #         # "published_at": model.published_at,
    #         "owner_id": model.owner_id,
    #         "owner_name": model.owner.username if model.owner else None,
    #         "image_url": image_url,
    #         "image_id": image_id,
    #         "module_count": count,
    #     }
        
    # staticmethod
    # def _load_modules(course_domain, model, lite_mode: bool = False):
    #     """
    #     Helper load module.
    #     lite_mode=True: Chỉ load Title, Duration (cho màn hình Preview)
    #     lite_mode=False: Load Full (cho màn hình Learning)
    #     """
    #     if hasattr(model, 'modules'):
    #         modules_sorted = sorted(model.modules.all(), key=lambda m: m.position)
    #         for module_model in modules_sorted:
    #             # ModuleDomain cần hỗ trợ method from_model(lite_mode=...)
    #             course_domain.modules.append(
    #                 ModuleDomain.from_model(module_model, lite_mode=lite_mode)
    #             )


    # # =========================================================================
    # # GROUP 1: END-USER VIEWS
    # # =========================================================================

    # @classmethod
    # def from_catalog_list(cls, model):
    #     """
    #     [CASE 1: LIST BÌNH THƯỜNG]
    #     Mục tiêu: Cực nhẹ. Hiển thị dạng Grid/Card.
    #     Không load Module. Chỉ lấy Meta + Ảnh + Tên GV.
    #     """
    #     data = cls._map_base_attributes(model)
        
    #     # Chỉ lấy tên category/tag string cho nhẹ JSON
    #     data["category_names"] = [cat.name for cat in model.categories.all()]
    #     data["tag_names"] = [tag.name for tag in model.tags.all()]
        
    #     return cls(**data)

    # @classmethod
    # def from_syllabus_preview(cls, model):
    #     """
    #     [CASE 2: XEM QUA / PREVIEW]
    #     Mục tiêu: Thuyết phục user mua/học. 
    #     Cần: Description chi tiết + Cấu trúc Mục lục (Syllabus) + Thống kê.
    #     Nhưng KHÔNG lộ URL video hay nội dung quiz.
    #     """
    #     data = cls._map_base_attributes(model)
        
    #     # 1. Load Stats (Moodle style: "Khoá này có 10 videos, 2 quizzes")
    #     data["stats"] = cls._get_course_stats(model)

    #     domain = cls(**data)

    #     # 2. Load Modules & Lessons nhưng ở chế độ "Skeleton" (Chỉ lấy Title)
    #     # Lưu ý: Hàm _load_modules cần được điều chỉnh để nhận flag 'lite_mode=True'
    #     # để LessonDomain chỉ map title, type, duration, không map video_url.
    #     cls._load_modules(domain, model, lite_mode=True) 

    #     return domain

    # @classmethod
    # def from_learning_detail(cls, model):
    #     """
    #     [CASE 3: VÀO HỌC CHÍNH THỨC]
    #     Mục tiêu: Học tập.
    #     Cần: Full data, Video URL, Quiz Questions, User Progress (nếu có).
    #     """
    #     data = cls._map_base_attributes(model)
    #     domain = cls(**data)
        
    #     # Load Full: Kèm theo file, link video, nội dung bài học
    #     cls._load_modules(domain, model, lite_mode=False)
        
    #     return domain

    # # =========================================================================
    # # GROUP 2: ADMIN VIEWS
    # # =========================================================================

    # @classmethod
    # def from_admin_list(cls, model):
    #     """
    #     [CASE 4: LIST ADMIN]
    #     Mục tiêu: Quản lý, Sort, Filter.
    #     Quan trọng: Created_at, Status, Owner, Metrics.
    #     Không cần: Description dài, Image (trừ khi cần icon nhỏ), Modules.
    #     """

    #     data = cls._map_base_attributes(model)
        
    #     # Chỉ lấy tên category/tag string cho nhẹ JSON
    #     data["created_at"] = model.created_at
    #     data["updated_at"] = model.updated_at
        
    #     return cls(**data)

    # @classmethod
    # def from_admin_detail(cls, model):
    #     """
    #     [CASE 5: ADMIN DETAIL]
    #     Mục tiêu: Kiểm duyệt nội dung, Debug.
    #     Giống Learning Detail nhưng thêm các thông tin hệ thống (Logs, Raw data).
    #     """
    #     data = cls._map_base_attributes(model)
    #     data["subject_obj"] = SubjectDomain.from_model(model.subject)
    #     data["category_objs"] = [CategoryDomain.from_model(c) for c in model.categories.all()]
    #     data["tag_objs"] = [TagDomain.from_model(t) for t in model.tags.all()]

    #     domain = cls(**data)
    #     cls._load_modules(domain, model)

    #     # Sử dụng lại logic admin cũ của bạn nhưng bổ sung stats
    #     # domain = cls.from_model_admin(model) # Tận dụng hàm cũ
    #     domain.stats = cls._get_course_stats(model)
    #     return domain


    # # @classmethod
    # # def from_model_overview(cls, model):
    # #     """
    # #     [STRATEGY: OVERVIEW]
    # #     Chỉ metadata + Tags/Categories dạng String.
    # #     """
    # #     data = cls._map_base_attributes(model)

    # #     data["category_names"] = [cat.name for cat in model.categories.all()]
    # #     data["tag_names"] = [tag.name for tag in model.tags.all()]

    # #     categories = list(model.categories.all())
    # #     tags = list(model.tags.all())

    # #     # Truyền vào key _objs để __init__ nhận diện
    # #     data["category_objs"] = categories
    # #     data["tag_objs"] = tags
        
    # #     return cls(**data)
    
    # # @classmethod
    # # def from_model(cls, model):
    # #     """
    # #     [STRATEGY: FULL_STRUCTURE]
    # #     Overview + Cấu trúc bài học (Modules -> Lessons).
    # #     Dùng cho màn hình Learning hoặc Instructor Edit.
    # #     """
    # #     # 1. Tái sử dụng Overview để lấy metadata & string tags
    # #     domain = cls.from_model_overview(model)
        
    # #     # 2. Load thêm Modules
    # #     cls._load_modules(domain, model)
        
    # #     return domain

    # # @classmethod
    # # def from_model_admin(cls, model):
    # #     """
    # #     [STRATEGY: ADMIN_DETAIL]
    # #     Metadata + Full Objects (User, Subject, Tags) + Modules.
    # #     Dùng cho Admin Dashboard.
    # #     """
    # #     # 1. Lấy khung sườn
    # #     data = cls._map_base_attributes(model)

    # #     # 2. Đắp thịt (Dạng Full Object "Giàu")       
    # #     if model.subject:
    # #         data["subject_obj"] = SubjectDomain.from_model(model.subject)

    # #     data["category_objs"] = [CategoryDomain.from_model(c) for c in model.categories.all()]
    # #     data["tag_objs"] = [TagDomain.from_model(t) for t in model.tags.all()]

    # #     # 3. Tạo object
    # #     domain = cls(**data)

    # #     # 4. Load thêm Modules (Admin cũng cần xem cấu trúc)
    # #     cls._load_modules(domain, model)

    # #     return domain
