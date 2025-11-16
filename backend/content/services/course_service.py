import uuid
import logging
from typing import Any, Dict, List
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Prefetch
from django.db import IntegrityError
from django.utils.text import slugify


from custom_account.models import UserModel 
from media.services import file_service
from media.models import UploadedFile
from content.models import Course
from content.domains.course_domain import CourseDomain
from content.domains import module_domain 
from content.services import module_service
from content.services.exceptions import DomainError, CourseNotFoundError, NotFoundError, InvalidOperation
from content.models import Course, Module, Lesson, Enrollment, Category, Tag



@transaction.atomic
def create_course(data: dict, owner) -> Course:
    """
    Hàm ĐIỀU PHỐI. Quản lý transaction cho toàn bộ quá trình.
    """
    # 1. Tách dữ liệu lồng nhau và M2M ra khỏi data chính
    modules_data = data.get('modules', [])
    categories_names = data.get('categories', [])
    tag_names = data.get('tags', [])
    image_url = data.get('image_url', None)
    
    # (Bạn có thể xử lý tags tương tự)
    
    # 2. Xử lý logic cho Course (ví dụ: tạo slug nếu thiếu)
    if 'slug' not in data or not data['slug']:
        data['slug'] = slugify(data['title'])
    # (Bạn nên có logic kiểm tra slug trùng ở đây)

    # 3. Tạo đối tượng gốc (Course)
    try:
        # Thay vì dùng **data, chúng ta liệt kê tường minh các trường
        # từ model 'Course' mà chúng ta mong đợi có trong 'data'.
        
        course = Course.objects.create(
            owner=owner,
            
            # Các trường được xử lý hoặc bắt buộc
            title=data['title'],  # Sẽ báo lỗi KeyError nếu thiếu (đây là điều tốt)
            slug=data['slug'],    # Đã được đảm bảo có từ Bước 2
            
            # Các trường tùy chọn (dùng .get() để an toàn)
            description=data.get('description'),
            grade=data.get('grade'),
            published=data.get('published', False), # Mặc định là False nếu thiếu
            
            # Xử lý ForeignKey tùy chọn (null=True, blank=True)
            # Model của bạn có 'subject'. Bạn cần quyết định cách 'data'
            # cung cấp thông tin này.
            
            # === CHỌN 1 TRONG 2 CÁCH SAU ===
            
            # Cách 1: Nếu data['subject'] là một object Subject (hoặc None)
            subject=data.get('subject')
            
            # Cách 2: Nếu data['subject_id'] là một UUID/int (hoặc None)
            # subject_id=data.get('subject_id') 
            
            # (Xóa dòng bạn không dùng)
        )
    
    except IntegrityError as e:
        # Bắt lỗi vi phạm ràng buộc CSDL (thường là do 'slug' bị trùng).
        raise ValueError(f"Slug '{data['slug']}' đã tồn tại. Vui lòng chọn một tiêu đề khác.")
    
    except KeyError as e:
        # Bắt lỗi nếu 'data' thiếu 'title' (hoặc 'slug' nếu Bước 2 lỗi)
        raise ValueError(f"Thiếu trường dữ liệu bắt buộc: {str(e)}")
    
    # 4. Xử lý M2M (Category)
    # (Phải tạo course trước mới gán M2M được)
    files_to_commit = []
    if image_url:
        files_to_commit.append(image_url)

    for tag_name in tag_names:
        # Tìm hoặc tạo Tag
        tag, _ = Tag.objects.get_or_create(
            name=tag_name, 
            defaults={'slug': slugify(tag_name)}
        )
        course.tags.add(tag)

    for cat_name in categories_names:
        # Tìm hoặc tạo Category
        category, _ = Category.objects.get_or_create(
            name=cat_name, 
            defaults={'slug': slugify(cat_name)}
        )
        course.categories.add(category)
    
    # 5. GỌI VÀ ỦY QUYỀN cho domain/service con
    # Đây là phần bạn đã làm đúng
    for module_data in modules_data:
        # Hàm con này KHÔNG cần transaction, vì nó đang chạy bên trong
        # transaction của hàm cha.
        module, module_files = module_service.create_module(
            course=course, 
            data=module_data
        )
        files_to_commit.extend(module_files) # Gom file để commit
    
    # 6. (Rất quan trọng) Commit file
    # Chỉ chạy khi toàn bộ 1-5 ở trên thành công
    # Nếu bước này lỗi, toàn bộ transaction (bước 3, 4, 5) sẽ
    # TỰ ĐỘNG ROLLBACK. Đây chính là sức mạnh của @transaction.atomic.
    try:
        file_service.commit_files_for_object(files_to_commit, course)
    except Exception as e:
        # Nếu commit file lỗi, chúng ta cần chủ động rollback DB
        # Bằng cách raise một Exception để @transaction.atomic bắt được
        raise ValueError(f"Lỗi khi commit file: {str(e)}")

    return course


def list_courses() -> List[CourseDomain]:
    """Lấy tất cả courses dưới dạng list các CourseDomain."""
    
    # Sử dụng prefetch_related để tối ưu M2M, tránh N+1 queries
    course_models = Course.objects.all().prefetch_related(
        'categories', 'tags'
    ).order_by('title')
    
    course_domains = [CourseDomain.from_model(course) for course in course_models]
    return course_domains


def get_course_by_id(course_id: uuid.UUID) -> CourseDomain:
    """Lấy một course theo ID."""
    try:
        # Tối ưu query bằng select_related và prefetch_related
        course = Course.objects.select_related(
            'owner', 'subject'
        ).prefetch_related(
            'categories', 'tags'
        ).get(pk=course_id)
        
        return CourseDomain.from_model(course)
        
    except ObjectDoesNotExist:
        raise CourseNotFoundError("Không tìm thấy khóa học.")
    except Exception as e:
        raise DomainError(f"Lỗi khi lấy khóa học: {e}")


@transaction.atomic
def update_course(course_id: uuid.UUID, updates: Dict[str, Any]) -> CourseDomain:
    """
    Cập nhật một course.
    'updates' là dict đã được validate (ví dụ: từ Pydantic DTO).
    """
    try:
        course = Course.objects.get(pk=course_id)
    except ObjectDoesNotExist:
        raise CourseNotFoundError("Không tìm thấy khóa học để cập nhật.")

    # 1. Tạo domain từ model (giống pattern của update_user)
    domain = CourseDomain.from_model(course)

    # 2. Tách riêng các trường M2M và FK
    category_ids = updates.pop('categories', None)
    tag_ids = updates.pop('tags', None)
    subject_id = updates.pop('subject', None)

    # 3. Áp dụng updates vào domain (để Pydantic/Domain validate)
    try:
        domain.apply_updates(updates)
    except (ValidationError, ValueError) as e:
        raise DomainError(f"Dữ liệu cập nhật không hợp lệ: {e}")

    # 4. Cập nhật các trường thông thường trên model
    for key, value in updates.items():
        if hasattr(course, key):
            setattr(course, key, value)

    # 5. Cập nhật trường FK
    if subject_id is not None:
        course.subject_id = subject_id # Giả sử 'subject' là ID
    
    course.save() # Lưu các thay đổi của trường thường và FK

    # 6. Cập nhật các trường M2M
    # (Giá trị 'None' nghĩa là 'không thay đổi', 
    # list rỗng [] nghĩa là 'xoá hết')
    if category_ids is not None:
        course.categories.set(category_ids)
    if tag_ids is not None:
        course.tags.set(tag_ids)

    # 7. Trả về domain đã được cập nhật
    # (Chúng ta cần re-fetch từ model để đảm bảo M2M data là chính xác)
    return CourseDomain.from_model(course)


logger = logging.getLogger(__name__)
@transaction.atomic
def delete_course_for_instructor(course_id: uuid.UUID, owner) -> None:
    """
    Xóa một khóa học và dọn dẹp TẤT CẢ các file liên quan.
    Chỉ owner (Instructor) mới được xóa.
    """
    
    # 1. Tìm và xác thực course (giống hàm delete của bạn)
    try:
        course = Course.objects.get(pk=course_id, owner=owner)
    except Course.DoesNotExist:
        raise CourseNotFoundError("Không tìm thấy khóa học hoặc bạn không có quyền xóa.")

    # 2. (QUAN TRỌNG) Dọn dẹp file vật lý
    #    Hàm create_course đã dùng ContentType để gán file,
    #    giờ chúng ta dùng nó để tìm lại file.
    
    try:
        # Tìm ContentType của model 'Course'
        course_content_type = ContentType.objects.get_for_model(course)
        
        # Tìm tất cả các bản ghi 'UploadedFile' đã được "commit"
        # cho chính đối tượng Course này (ảnh bìa, file pdf, v.v.)
        linked_files = UploadedFile.objects.filter(
            content_type=course_content_type, 
            object_id=course.pk
        )

        # Gọi 'file_service.delete_file' cho từng file
        # (Hàm 'delete_file' của bạn đã tự xử lý việc xóa file vật lý)
        for file_record in linked_files:
            file_service.delete_file(file_record.pk)
            
    except Exception as e:
        # Nếu xóa file lỗi, chúng ta rollback toàn bộ
        logger.error(f"Lỗi khi dọn dẹp file cho Course {course_id}: {e}", exc_info=True)
        raise DomainError(f"Lỗi khi dọn dẹp file: {e}")

    # 3. Xóa bản ghi CSDL (và để CASCADE lo phần còn lại)
    #    Phải làm sau cùng, sau khi đã xóa file thành công.
    course.delete()
    return None


def get_course(course_id: str) -> CourseDomain:
    """
    Hàm "Repository Get" chính.
    Lấy một Course Aggregate Root đầy đủ, bao gồm modules, lessons, versions,
    categories, và tags.
    """
    try:
        # 1. Xây dựng câu query prefetch lồng nhau
        # Điều này là BẮT BUỘC để `CourseDomain.from_model` 
        # và `can_publish` hoạt động mà không gây N+1 queries.
        
        course_model = Course.objects.select_related(
            'owner', 'subject' # Tối ưu FK
        ).prefetch_related(
            'categories', 'tags', # Tối ưu M2M (cho from_model)
            Prefetch(
                'modules', # Giả định related_name='modules' (đúng)
                queryset=Module.objects.all().order_by('position').prefetch_related(
                    Prefetch(
                        'lessons', # Giả định related_name='lessons' (đúng)
                        queryset=Lesson.objects.all().order_by('position')
                    )
                )
            )
        ).get(id=course_id)
        
        # 2. Gán list modules đã prefetch vào thuộc tính 
        # mà `CourseDomain.from_model` của bạn mong đợi
        course_model.modules_prefetched = course_model.modules.all()

        # 3. "Nạp" (hydrate) aggregate root
        return CourseDomain.from_model(course_model)

    except Course.DoesNotExist:
        raise NotFoundError("Không tìm thấy khóa học.")
    except Exception as e:
        # Bắt các lỗi khác (ví dụ: related_name sai, lỗi logic from_model)
        raise DomainError(f"Lỗi khi tải course aggregate: {e}")


@transaction.atomic
def publish_course(course_id: str, publish_data: Any) -> CourseDomain:
    """
    Publish một course. Áp dụng các quy tắc nghiệp vụ trong Domain.
    """
    # 1. Lấy Aggregate Root (đã bao gồm tất cả modules/lessons)
    course_domain = get_course(course_id)
    
    # 2. Lấy cờ (flag) từ command (view của bạn truyền vào)
    require_all = getattr(publish_data, 'require_all_lessons_published', False)
    
    # 3. Gọi logic nghiệp vụ (Domain)
    # Hàm này sẽ ném ra InvalidOperation nếu quy tắc 'can_publish' thất bại
    try:
        course_domain.publish(require_all_lessons_published=require_all)
    except InvalidOperation as e:
        # Re-raise lỗi nghiệp vụ để view xử lý (HTTP 400)
        raise e
    
    # 4. Lưu trạng thái mới vào DB (Repository Save)
    try:
        # Lấy model instance để lưu
        course_model = Course.objects.get(id=course_id)
        
        # Đồng bộ trạng thái từ domain (đã được sửa)
        course_model.published = course_domain.published
        course_model.published_at = course_domain.published_at # Đây là datetime

        course_model.save(update_fields=['published', 'published_at'])
        
        return course_domain
        
    except Course.DoesNotExist:
        raise NotFoundError("Không tìm thấy khóa học để lưu.")
    except Exception as e:
        raise DomainError(f"Lỗi khi lưu trạng thái publish: {e}")


@transaction.atomic
def unpublish_course(course_id: str) -> CourseDomain:
    """
    Unpublish một course.
    """
    # 1. Lấy Aggregate Root
    course_domain = get_course(course_id)
    
    # 2. Gọi logic nghiệp vụ (Domain)
    course_domain.unpublish() # Hàm này sẽ set published=False, published_at=None
    
    # 3. Lưu trạng thái mới vào DB (Repository Save)
    try:
        course_model = Course.objects.get(id=course_id)
        
        # Đồng bộ trạng thái từ domain
        course_model.published = course_domain.published
        course_model.published_at = course_domain.published_at # Đây là None

        course_model.save(update_fields=['published', 'published_at'])
        
        # View của bạn kiểm tra 'if not updated:',
        # nên chúng ta trả về domain object
        return course_domain
        
    except Course.DoesNotExist:
        raise NotFoundError("Không tìm thấy khóa học để lưu.")
    except Exception as e:
        raise DomainError(f"Lỗi khi lưu trạng thái unpublish: {e}")


def enroll_user(course_id: str, user_id: int) -> Enrollment:
    """
    Ghi danh user hiện tại vào course.
    Sử dụng model `Enrollment` mới.
    """
    try:
        # Lấy user và course (là 2 FK của Enrollment)
        user = UserModel.objects.get(id=user_id)
        course = Course.objects.get(id=course_id)
    except (UserModel.DoesNotExist, Course.DoesNotExist):
        raise NotFoundError("Không tìm thấy User hoặc Course.")
    
    # Kiểm tra logic nghiệp vụ (ví dụ: course phải được publish)
    if not course.published:
        raise InvalidOperation("Không thể ghi danh vào khóa học chưa publish.")

    try:
        # get_or_create đảm bảo không ghi danh 2 lần
        # (Lợi dụng unique_together đã định nghĩa trong model)
        enrollment, created = Enrollment.objects.get_or_create(
            user=user,
            course=course
        )
        return enrollment
    except Exception as e:
        # Bắt các lỗi DB khác
        raise DomainError(f"Lỗi khi ghi danh: {e}")


def unenroll_user(course_id: str, user_id: int) -> bool:
    """
    Hủy ghi danh user khỏi course.
    """
    try:
        # Xóa các bản ghi enrollment khớp
        # Dùng .delete() hiệu quả hơn là .get() rồi .delete()
        deleted_count, _ = Enrollment.objects.filter(
            user_id=user_id,
            course_id=course_id
        ).delete()
        
        if deleted_count == 0:
            # Không có gì để xóa
            raise NotFoundError("Không tìm thấy bản ghi ghi danh để xóa.")
            
        return True
    except Exception as e:
        raise DomainError(f"Lỗi khi hủy ghi danh: {e}")
    

def list_courses_for_instructor(owner: UserModel) -> List[CourseDomain]:
    """
    CHỈ lấy các course thuộc sở hữu của một instructor.
    """
    course_models = Course.objects.filter(owner=owner).prefetch_related(
        'categories', 'tags'
    ).order_by('title')
    
    course_domains = [CourseDomain.from_model(course) for course in course_models]
    return course_domains


# def get_course_by_id_for_instructor(course_id: uuid.UUID, owner: UserModel) -> CourseDomain:
#     """
#     Lấy một course theo ID, check quyền sở hữu, VÀ tải trước (prefetch)
#     toàn bộ cây dữ liệu (modules, lessons, files...) để tối ưu hiệu suất.
#     """
#     try:
#         # Chúng ta sẽ prefetch theo từng cấp.
#         # Giả định bạn có trường 'order' (hoặc 'created_at') để sắp xếp.
        
#         # Cấp 3: Nội dung chi tiết (ví dụ: Explorations) và file của chúng
#         # (Nếu không có cấp này, bạn có thể bỏ qua)
#         prefetch_explorations = Prefetch(
#             'explorations', # Tên related_name từ Lesson -> Exploration
#             queryset=Exploration.objects.order_by('order').prefetch_related('files'),
#             to_attr='ordered_explorations' # Gán vào thuộc tính mới
#         )

#         # Cấp 2: Lessons và file của chúng (và cả cấp 3 bên trong)
#         prefetch_lessons = Prefetch(
#             'lessons', # Tên related_name từ Module -> Lesson
#             queryset=Lesson.objects.order_by('order').prefetch_related(
#                 'files', # File đính kèm của Lesson
#                 prefetch_explorations # Lồng prefetch của cấp 3
#             ),
#             to_attr='ordered_lessons'
#         )

#         # Cấp 1: Modules và file của chúng (và cả cấp 2 bên trong)
#         prefetch_modules = Prefetch(
#             'modules', # Tên related_name từ Course -> Module
#             queryset=Module.objects.order_by('order').prefetch_related(
#                 'files', # File đính kèm của Module
#                 prefetch_lessons # Lồng prefetch của cấp 2
#             ),
#             to_attr='ordered_modules'
#         )

#         # Cấp 0: Course (đối tượng gốc)
#         course = Course.objects.select_related(
#             'owner', 'subject'
#         ).prefetch_related(
#             'categories', 
#             'tags',
            
#             # --- Phần thêm mới ---
            
#             # 1. File đính kèm TRỰC TIẾP với Course (ví dụ: ảnh bìa)
#             # (Giả định bạn đã thêm GenericRelation 'files' vào model Course)
#             'files', 
            
#             # 2. Toàn bộ cây nội dung đã được định nghĩa ở trên
#             prefetch_modules
            
#         ).get(pk=course_id, owner=owner) 
        
#         # Bây giờ, khi CourseDomain.from_model(course) chạy,
#         # nó có thể truy cập course.ordered_modules,
#         # và mỗi module trong đó có .ordered_lessons,
#         # và mỗi lesson có .ordered_explorations (nếu có) và .files
#         # ... mà không cần truy vấn CSDL thêm một lần nào nữa.
        
#         # Bạn CẦN cập nhật CourseDomain.from_model để đọc từ
#         # 'ordered_modules' thay vì 'modules.all()',
#         # 'ordered_lessons' thay vì 'lessons.all()', v.v.
        
#         return CourseDomain.from_model(course)
        
#     except ObjectDoesNotExist:
#         raise CourseNotFoundError("Không tìm thấy khóa học.")
#     except Exception as e:
#         logger.error(f"Lỗi khi lấy chi tiết khóa học {course_id}: {e}", exc_info=True)
#         raise DomainError(f"Lỗi khi lấy khóa học: {e}")


@transaction.atomic
def update_course_for_instructor(course_id: uuid.UUID, updates: Dict[str, Any], owner: UserModel) -> CourseDomain:
    """
    Cập nhật một course, NHƯNG phải check quyền sở hữu.
    """
    # 1. Kiểm tra sự tồn tại và quyền sở hữu
    try:
        course_check = Course.objects.get(pk=course_id, owner=owner) 
    except ObjectDoesNotExist:
        raise CourseNotFoundError("Không tìm thấy khóa học để cập nhật.")

    # 2. Nếu đã qua check quyền, gọi hàm update_course chung
    return update_course(course_id=course_id, updates=updates)


# --- CÁC HÀM AGGREGATE (PUBLISH/UNPUBLISH) CHO INSTRUCTOR ---

def get_course_for_instructor(course_id: str, owner: UserModel) -> CourseDomain:
    """
    """
    try:
        # Bắt đầu query từ hàm get_course (đã prefetch)
        # và thêm bộ lọc 'owner'
        course_model = (Course.objects
            .select_related('owner', 'subject')
            .prefetch_related(
                'categories', 'tags',
                Prefetch('modules', queryset=Module.objects.all().order_by('position').prefetch_related(
                    Prefetch('lessons', queryset=Lesson.objects.all().order_by('position'))
                ))
            )
            .get(id=course_id, owner=owner) # <
        )
        
        course_model.modules_prefetched = course_model.modules.all()
        return CourseDomain.from_model(course_model)

    except Course.DoesNotExist:
        raise NotFoundError("Không tìm thấy khóa học.")
    except Exception as e:
        raise DomainError(f"Lỗi khi tải course aggregate: {e}")


@transaction.atomic
def publish_course_for_instructor(course_id: str, publish_data: Any, owner: UserModel) -> CourseDomain:
    """
    Publish một course
    """
    # Lấy Aggregate Root (đã check quyền sở hữu)
    course_domain = get_course_for_instructor(course_id, owner)
    
    # Gọi hàm publish 
    require_all = getattr(publish_data, 'require_all_lessons_published', False)
    try:
        course_domain.publish(require_all_lessons_published=require_all)
    except InvalidOperation as e:
        raise e
    
    # Lưu trạng thái 
    try:
        course_model = Course.objects.get(id=course_id, owner=owner) 
        course_model.published = course_domain.published
        course_model.published_at = course_domain.published_at
        course_model.save(update_fields=['published', 'published_at'])
        return course_domain
    except Course.DoesNotExist:
        raise NotFoundError("Không tìm thấy khóa học để lưu.")
    except Exception as e:
        raise DomainError(f"Lỗi khi lưu trạng thái publish: {e}")


@transaction.atomic
def unpublish_course_for_instructor(course_id: str, owner: UserModel) -> CourseDomain:
    """
    Unpublish một course
    """
    # Lấy Aggregate Root (đã check quyền sở hữu)
    course_domain = get_course_for_instructor(course_id, owner)
    
    # Gọi logic unpublish
    course_domain.unpublish()
    
    # Lưu trạng thái
    try:
        course_model = Course.objects.get(id=course_id, owner=owner) 
        course_model.published = course_domain.published
        course_model.published_at = course_domain.published_at
        course_model.save(update_fields=['published', 'published_at'])
        return course_domain
    except Course.DoesNotExist:
        raise NotFoundError("Không tìm thấy khóa học để lưu.")
    except Exception as e:
        raise DomainError(f"Lỗi khi lưu trạng thái unpublish: {e}")


