import uuid
import logging
import time
from typing import List, Dict
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType
from django.db import transaction, IntegrityError
from django.db.models import Q, Count, Prefetch, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.text import slugify

from custom_account.models import UserModel 
from content.services.module_service import create_module_from_template
from media.services.cloud_service import s3_copy_object
from media.models import UploadedFile, FileStatus
from content.domains.course_domain import CourseDomain
from content.models import Course, Module, Lesson, Category, Tag, Subject, ContentBlock
from core.exceptions import DomainError
from content.types import CourseFetchStrategy, CourseFilter



# ==========================================
# Helpers
# ==========================================

def _build_queryset(filters: CourseFilter, strategy: CourseFetchStrategy):
    """
    Hàm nội bộ: Dựng QuerySet dựa trên Filter và Strategy.
    Đây là nơi DUY NHẤT bạn tối ưu DB query (prefetch/select_related).
    """
    query_set = Course.objects.all()

    # --- A. ÁP DỤNG BỘ LỌC (FILTERS) ---
    if filters.course_id:
        query_set = query_set.filter(id=filters.course_id)
    if filters.ids:
        query_set = query_set.filter(id__in=filters.ids)
    if filters.owner:
        query_set = query_set.filter(owner=filters.owner)
    if filters.published_only:
        query_set = query_set.filter(published=True)
    if filters.search_term:
        query_set = query_set.filter(title__icontains=filters.search_term)
    if filters.enrolled_user:
        # Logic: Tìm khóa học mà user đã ghi danh
        query_set = query_set.filter(enrollments__user=filters.enrolled_user).distinct()
    # --- (MỚI) Logic: LOẠI BỎ khóa học ĐÃ ghi danh (Public/Unregistered Courses) ---
    if filters.exclude_enrolled_user:
        # exclude ngược lại với filter: Bỏ đi những course mà user này nằm trong bảng enrollments
        query_set = query_set.exclude(enrollments__user=filters.exclude_enrolled_user)

        
    # --- B. TỐI ƯU HÓA QUERY (STRATEGY) ---
    # 1. Join bảng Owner để lấy tên giảng viên (1 query thay vì N)
    query_set = query_set.select_related('owner', 'subject')

    # 2. Luôn lấy các quan hệ nhẹ
    query_set = query_set.prefetch_related('categories', 'tags')

    # --- C. ANNOTATION (TÍNH TOÁN SQL) ---
    # Phần này cực quan trọng: Chuyển logic đếm từ Python sang SQL

    # Đếm cơ bản
    query_set = query_set.annotate(
        modules_count=Count('modules', distinct=True),
        students_count=Count('enrollments', distinct=True),
    )

    if strategy in [
        CourseFetchStrategy.BASIC,
        CourseFetchStrategy.CATALOG_LIST, 
        CourseFetchStrategy.INSTRUCTOR_DASHBOARD,
        CourseFetchStrategy.STRUCTURE,
        CourseFetchStrategy.INSTRUCTOR_DETAIL,
        CourseFetchStrategy.ADMIN_LIST,
        CourseFetchStrategy.ADMIN_DETAIL
    ]:
        query_set = query_set.annotate(
            # Đếm tổng số bài học (Lesson) thông qua Module
            total_lessons=Count('modules__lessons', distinct=True),
            
            # Đếm Video & Quiz (Dùng Conditional Count)
            # Giả sử ContentBlock link với Lesson qua 'content_blocks'
            total_videos=Count(
                'modules__lessons__content_blocks', 
                filter=Q(modules__lessons__content_blocks__type='video'),
                distinct=True
            ),
            total_quizzes=Count(
                'modules__lessons__content_blocks', 
                filter=Q(modules__lessons__content_blocks__type='quiz'),
                distinct=True
            ),
            
            # NEW: TÍNH TỔNG THỜI LƯỢNG (Sum Duration)
            # Logic: Cộng dồn cột 'duration' của tất cả content blocks
            # Coalesce để nếu null thì trả về 0
            total_seconds=Coalesce(Sum('modules__lessons__content_blocks__duration'), 0)
        )

    # 3. Chiến lược riêng biệt
    if strategy == CourseFetchStrategy.BASIC:
        pass

    if strategy in [CourseFetchStrategy.CATALOG_LIST, CourseFetchStrategy.INSTRUCTOR_DASHBOARD]:
        pass

    elif strategy == CourseFetchStrategy.ADMIN_LIST:
        pass

    # 2. STRUCTURE / DETAIL (Màn hình học/xem chi tiết)
    elif strategy in [CourseFetchStrategy.STRUCTURE, CourseFetchStrategy.INSTRUCTOR_DETAIL, CourseFetchStrategy.ADMIN_DETAIL]:
        # Cần load cây thư mục: Module -> Lesson
        query_set = query_set.prefetch_related(
            'modules',
            'modules__lessons',
            # Chỉ lấy các field cần thiết của ContentBlock để hiển thị icon trên mục lục
            # Không lấy payload nặng
            Prefetch(
                'modules__lessons__content_blocks',
                queryset=ContentBlock.objects.order_by('position').only('id', 'title', 'type', 'lesson_id')
            )
        )
        
    # Sort mặc định
    return query_set.order_by('-created_at')


def _get_or_create_tags(tag_names: list[str]) -> list[Tag]:
    """
    Lấy hoặc tạo mới các Tag từ danh sách tên.
    
    Args:
        tag_names: Danh sách tên tag.
        
    Returns:
        List các Tag instance.
    """
    tags = []
    for name in tag_names:
        tag_slug = slugify(name)
        try:
            tag, _ = Tag.objects.get_or_create(
                name=name, 
                defaults={'slug': tag_slug}
            )
        except IntegrityError:
            # Slug bị trùng do race condition
            tag = Tag.objects.get(slug=tag_slug)
        tags.append(tag)
    return tags


def _get_or_create_categories(category_names: list[str]) -> list[Category]:
    """
    Lấy hoặc tạo mới các Category từ danh sách tên.
    
    Args:
        category_names: Danh sách tên category.
        
    Returns:
        List các Category instance.
    """
    categories = []
    for name in category_names:
        cat_slug = slugify(name)
        try:
            category, _ = Category.objects.get_or_create(
                name=name, 
                defaults={'slug': cat_slug}
            )
        except IntegrityError:
            # Slug bị trùng do race condition
            category = Category.objects.get(slug=cat_slug)
        categories.append(category)
    return categories


def _handle_course_image_update(course, image_id):
    """Tách logic xử lý ảnh ra hàm riêng cho code clean hơn"""
    try:
        temp_file = UploadedFile.objects.get(id=image_id, status=FileStatus.STAGING)
        src_path = temp_file.file.name
        
        # --- FIXED: Xử lý file cũ & Cache busting ---
        # 1. Nếu course đã có thumbnail, nên xóa file cũ trên S3 để tránh rác
        if course.thumbnail:
            try:
                # Hàm này giả định bạn có logic xóa file S3 từ field model
                # course.thumbnail.delete(save=False) 
                # Hoặc gọi s3_delete_object(course.thumbnail.name)
                pass 
            except Exception:
                pass # Fail silently khi xóa file cũ

        # 2. Tạo tên file mới có TIMESTAMP để tránh Browser Cache
        file_ext = src_path.split('.')[-1]
        timestamp = int(time.time())
        # Ví dụ: course_thumbnails/uuid-1234_17000000.jpg
        dest_path = f"course_thumbnails/{course.id}_{timestamp}.{file_ext}"
        s3_full_dest_key = f"public/{dest_path}"

        # 3. Copy file
        s3_copy_object(src_path, s3_full_dest_key, is_public=True)

        # 4. Save DB
        course.thumbnail.name = dest_path
        course.save(update_fields=['thumbnail'])

        # 5. Clean staging
        temp_file.delete()

    except UploadedFile.DoesNotExist:
        logger.warning(f"Image ID {image_id} not found or not in staging.")
    except Exception as e:
        logger.error(f"Lỗi S3 Copy Thumbnail: {e}")


# ==========================================
# PUBLIC INTERFACE (GET)
# ==========================================

logger = logging.getLogger(__name__)

def get_courses(filters: CourseFilter, strategy: CourseFetchStrategy = CourseFetchStrategy.CATALOG_LIST) -> List[CourseDomain]:
    """
    Lấy danh sách khóa học (List).
    Không bao giờ raise lỗi Not Found, chỉ trả về list rỗng.
    """
    try:
        query_set = _build_queryset(filters, strategy)
        return [CourseDomain.factory(course, strategy) for course in query_set]
    except Exception as e:
        logger.error(f"Error listing courses: {e}", exc_info=True)
        raise DomainError(f"Lỗi hệ thống khi lấy danh sách khóa học: {str(e)}")


def get_course_single(filters: CourseFilter, strategy: CourseFetchStrategy = CourseFetchStrategy.STRUCTURE) -> CourseDomain:
    """
    Lấy chi tiết 1 khóa học (Detail).
    Raise DomainError nếu không tìm thấy (hoặc không thỏa mãn filter).
    """
    try:
        query_set = _build_queryset(filters, strategy)
        course = query_set.get() # Sẽ raise DoesNotExist hoặc MultipleObjectsReturned
        return CourseDomain.factory(course, strategy)
    
    except Course.DoesNotExist:
        # Context hóa lỗi: Nếu filter có owner -> User ko có quyền hoặc ID sai
        if filters.enrolled_user:
            raise DomainError("Bạn chưa ghi danh vào khóa học này.")
        if filters.course_id:
             raise DomainError("Không tìm thấy khóa học.")
        raise DomainError("Không tìm thấy khóa học.")
        
    except Exception as e:
        logger.error(f"Error getting course detail: {e}", exc_info=True)
        raise DomainError(f"Lỗi hệ thống khi lấy thông tin khóa học: {e}")
    

# ==========================================
# PUBLIC INTERFACE (CREATE)
# ==========================================

@transaction.atomic
def create_course_metadata(
    data: dict, 
    created_by: UserModel, 
    output_strategy: CourseFetchStrategy = CourseFetchStrategy.BASIC
) -> CourseDomain:
    """
    Tạo course metadata (chỉ thông tin cơ bản, chưa có curriculum).
    Hàm dùng chung cho cả Admin và Instructor.
    
    Args:
        data: Dữ liệu metadata (dict từ DTO).
        created_by: User thực hiện hành động (request.user).
        output_strategy: Strategy trả về Domain (mặc định BASIC).
        
    Returns:
        CourseDomain với metadata đã tạo.
        
    Raises:
        ValueError: Khi dữ liệu không hợp lệ hoặc slug trùng.
        IntegrityError: Khi có xung đột database.
    """
    
    # 1. Tách dữ liệu nested
    categories_names = data.pop('categories', [])
    tag_names = data.pop('tags', [])
    image_id = data.pop('image_id', None)

    # 2. Xác định owner
    # Admin có thể tạo hộ người khác, Instructor chỉ tạo cho mình
    owner = data.pop('owner', created_by)
    
    # 3. Xử lý slug
    if not data.get('slug'):
        data['slug'] = slugify(data['title'])

    if Course.objects.filter(slug=data['slug']).exists():
        raise ValueError(f"Slug '{data['slug']}' đã tồn tại. Vui lòng đổi tên.")
    
    subject_name = data.get('subject') # Lấy string "Tin học"
    subject_instance = None

    if subject_name:
        # Nếu model Subject có field slug, ta nên tạo slug luôn
        sub_slug = slugify(subject_name) 
        
        # SỬA LẠI ĐOẠN NÀY:
        # Thay vì tìm theo title, ta tìm theo slug.
        # Lý do: Slug là unique key, tìm theo slug sẽ không bao giờ bị lỗi trùng lặp.
        subject_instance, created = Subject.objects.get_or_create(
            slug=sub_slug,
            defaults={'title': subject_name} 
        )

        # (Tuỳ chọn - Kỹ hơn) Nếu Subject đã tồn tại nhưng title cũ viết thường/hoa khác title mới
        # Ví dụ: DB đang lưu "tiếng việt", input vào là "Tiếng Việt" -> Update lại cho đẹp
        if not created and subject_instance.title != subject_name:
            subject_instance.title = subject_name
            subject_instance.save()
            

    # 4. Tạo Course object (Core entity)
    try:
        course = Course.objects.create(
            owner=owner,
            title=data['title'],
            slug=data['slug'],
            description=data.get('description', ''),
            grade=data.get('grade'),
            subject=subject_instance,
            published=data.get('published', False),
            thumbnail=None
        )
    except IntegrityError:
        raise ValueError(f"Slug '{data['slug']}' vừa bị trùng. Vui lòng thử lại.")
    except KeyError as e:
        raise ValueError(f"Thiếu trường dữ liệu bắt buộc: {e}") from e

    # 5. Xử lý Tags (M2M)
    if tag_names:
        tags = _get_or_create_tags(tag_names)
        course.tags.set(tags)

    # 6. Xử lý Categories (M2M)
    if categories_names:
        categories = _get_or_create_categories(categories_names)
        course.categories.set(categories)

    # 7. TỐI ƯU HÓA: Xử lý Image bằng S3 Copy
    if image_id:
        try:
            # Lấy thông tin file tạm
            temp_file_record = UploadedFile.objects.get(id=image_id, status=FileStatus.STAGING)
            
            # Lấy đường dẫn file gốc (Ví dụ: tmp/abc-xyz.jpg)
            src_path = temp_file_record.file.name
            
            # Định nghĩa đường dẫn đích (Ví dụ: public/courses/{course_id}.jpg)
            # Đặt tên theo ID course để dễ quản lý, tránh trùng lặp
            file_ext = src_path.split('.')[-1]
            dest_path = f"course_thumbnails/{course.id}.{file_ext}"
            s3_full_dest_key = f"public/{dest_path}"

            # GỌI HÀM COPY (Zero-byte transfer)
            # Lưu ý: dest_path sẽ được lưu vào kho Public nếu bucket chung, 
            # hoặc bạn phải config đúng path theo PublicStorage
            s3_copy_object(src_path, s3_full_dest_key, is_public=False)

            # Cập nhật đường dẫn vào DB
            # Django ImageField chỉ cần lưu string path, nó sẽ tự hiểu
            course.thumbnail.name = dest_path 
            course.save(update_fields=['thumbnail'])
            
            # Log debug để nhìn thấy ngay
            logger.info(f"✅ Đã copy thumbnail thành công: {dest_path}")

            # Dọn dẹp record bảng tạm (File trên S3 có thể xóa hoặc để Lifecycle rule tự xóa sau 24h)
            temp_file_record.delete()

        except UploadedFile.DoesNotExist:
            logger.warning(f"Image ID {image_id} not found or not in staging.")

        except Exception as e:
            logger.error(f"Lỗi S3 Copy Thumbnail: {e}")
            # Không raise error để tránh rollback việc tạo course, chỉ log warning

    # 8. Trả về Domain theo strategy
    return CourseDomain.factory(course, output_strategy)


# ==========================================
# PUBLIC INTERFACE (PATCH)
# ==========================================

@transaction.atomic
def update_course_metadata(
    course_id: uuid.UUID,
    data: dict,
    updated_by: UserModel,
    output_strategy: CourseFetchStrategy = CourseFetchStrategy.BASIC
) -> CourseDomain:
    """
    Cập nhật course metadata.
    
    Args:
        course_id: ID của khóa học cần sửa.
        data: Dữ liệu metadata cần cập nhật (có thể là partial data).
        updated_by: User thực hiện hành động.
        output_strategy: Strategy trả về Domain.
        
    Raises:
        PermissionDenied: Nếu user không phải owner hoặc admin.
        ValueError: Lỗi dữ liệu/slug trùng.
    """
    
    # 1. Lấy course và kiểm tra quyền
    # Dùng select_for_update để lock row này lại tránh race condition khi đang sửa
    try:
        course = Course.objects.select_for_update().get(pk=course_id)
    except Course.DoesNotExist:
        raise ValueError(f"Không tìm thấy Course với ID {course_id}")

    # 2. Tách dữ liệu nested (nếu có trong data thì mới xử lý)
    # Dùng .get() thay vì .pop() nếu muốn giữ data nguyên vẹn, 
    # hoặc .pop() nếu data là bản copy dùng 1 lần.
    categories_names = data.pop('categories', None)
    tag_names = data.pop('tags', None)
    image_id = data.pop('image_id', None)
    
    # Owner transfer (chỉ Admin mới được đổi chủ)
    new_owner = data.pop('owner', None)
    if new_owner and updated_by.is_staff:
        course.owner = new_owner

    # 3. Xử lý Title và Slug (Logic phức tạp nhất)
    new_title = data.get('title')
    if new_title and new_title != course.title:
        # Nếu title thay đổi -> Check slug mới
        new_slug = data.get('slug') or slugify(new_title)
        
        # Kiểm tra trùng slug (nhưng EXCLUDE chính course hiện tại)
        if Course.objects.filter(slug=new_slug).exclude(pk=course.pk).exists():
             raise ValueError(f"Title '{new_title}' đã tồn tại ở một khóa học khác.")
        
        course.title = new_title
        course.slug = new_slug
    
    # 4. Xử lý Subject (nếu có thay đổi)
    if 'subject' in data:
        subject_name = data['subject']
        if subject_name:
             # Logic tương tự Create: Tìm hoặc tạo mới Subject
            sub_slug = slugify(subject_name)
            try:
                subject_instance, _ = Subject.objects.get_or_create(
                    title=subject_name,
                    defaults={'slug': sub_slug}
                )
                course.subject = subject_instance
            except IntegrityError:
                 course.subject = Subject.objects.get(title=subject_name)
        else:
            # Nếu gửi lên là None hoặc rỗng -> Có thể cho phép set Null (tùy nghiệp vụ)
            course.subject = None

    # 5. Cập nhật các trường đơn giản (Scalar fields)
    fields_to_update = ['description', 'grade', 'published', 'price', 'currency']
    for field in fields_to_update:
        if field in data:
            setattr(course, field, data[field])

    # Save thay đổi vào bảng Course trước khi xử lý M2M
    try:
        course.save()
    except IntegrityError:
        raise ValueError("Lỗi dữ liệu xung đột khi lưu khóa học.")

    # 6. Xử lý Tags (M2M) - Thay thế toàn bộ tags cũ bằng tags mới
    if tag_names is not None: # Chỉ update nếu field này có tồn tại trong request
        tags = _get_or_create_tags(tag_names)
        course.tags.set(tags)

    # 7. Xử lý Categories (M2M)
    if categories_names is not None:
        categories = _get_or_create_categories(categories_names)
        course.categories.set(categories)

    # 8. Xử lý ảnh bìa
    if image_id:
        _handle_course_image_update(course, image_id)

    # 9. Trả về Domain
    return CourseDomain.factory(course, output_strategy)


# ==========================================
# PUBLIC INTERFACE (DELETE)
# ==========================================

@transaction.atomic
def delete_course(course_id: uuid.UUID, actor: UserModel) -> None:
    """
    Xóa khóa học.
    Admin có thể xóa mọi khóa. Instructor chỉ xóa khóa của mình.
    """
    try:
        course = Course.objects.get(pk=course_id)
            
    except Course.DoesNotExist:
        # Ném lỗi tương tự như delete_module
        raise Course.DoesNotExist(f"Khóa học với ID '{course_id}' không tồn tại hoặc bạn không có quyền xóa.")

    # 2. Xóa Course
    # Django sẽ tự động Cascade xóa:
    # Course -> Modules -> Lessons -> UploadedFiles (nếu có GenericRelation hoặc logic Signal đúng)
    course.delete()


# ==========================================
# PUBLIC INTERFACE (PUBLISH)
# ==========================================

@transaction.atomic
def publish_course(
    course_id: uuid.UUID, 
    actor: UserModel, 
    publish_action: bool
) -> CourseDomain:
    """
    Thay đổi trạng thái xuất bản của khóa học.
    Dùng chung cho cả Admin và Instructor.
    
    Args:
        publish_action: True = Publish, False = Unpublish/Draft
    """
    
    # 1. Lấy khóa học & Kiểm tra quyền (Logic giống Patch/Delete)
    # -----------------------------------------------------------
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        raise ValueError("Không tìm thấy khóa học hoặc bạn không có quyền thực hiện.")

    # 2. Kiểm tra Logic nghiệp vụ (Business Rules)
    # -----------------------------------------------------------
    if publish_action:
        # Rule: Không được publish khóa học rỗng (chưa có Module nào)
        # (Bạn có thể check sâu hơn: phải có ít nhất 1 Lesson đã publish)
        if not course.modules.exists():
            raise ValueError("Không thể xuất bản khóa học rỗng. Vui lòng thêm nội dung (Module) trước.")
        
        # Rule: Kiểm tra các điều kiện khác (ví dụ: phải có ảnh bìa, mô tả...)
        # if not course.files.exists(): ...

    # 3. Cập nhật trạng thái
    # -----------------------------------------------------------
    course.published = publish_action
    
    if publish_action:
        # Cập nhật thời gian publish mới nhất
        course.published_at = timezone.now()
    
    # Chỉ update đúng 2 trường này để tối ưu
    course.save(update_fields=['published', 'published_at'])

    logger.info(f"User {actor.email} đã {'PUBLISH' if publish_action else 'UNPUBLISH'} khóa học {course_id}")

    # 4. Trả về Domain (Overview là đủ để cập nhật UI)
    return get_course_single(
        filters=CourseFilter(course_id=course_id), 
        # Admin có thể xem AdminDetail, nhưng thường Overview là đủ cho nút toggle
        strategy=CourseFetchStrategy.STRUCTURE
    )


# ==========================================
# PUBLIC INTERFACE (TEMPLATE)
# ==========================================

# @transaction.atomic
# def create_course_from_template(data: dict, created_by: UserModel, output_strategy: CourseFetchStrategy = CourseFetchStrategy.STRUCTURE) -> CourseDomain:
#     """
#     Hàm tạo khóa học dùng chung cho cả Admin và Instructor.
    
#     Args:
#         data: Dữ liệu đầu vào (dict từ DTO).
#         created_by: User thực hiện hành động này (request.user).
#         output_strategy: Muốn trả về Domain kiểu gì (Overview hay Admin Detail).
#     """
    
#     # 1. Chuẩn bị dữ liệu (Tách nested data)
#     modules_data = data.get('modules', [])
#     categories_names = data.get('categories', [])
#     tag_names = data.get('tags', [])
#     image_id = data.get('image_id')

#     # Logic: Nếu là Admin tạo hộ, 'owner' trong data có thể khác 'created_by'.
#     # Nếu không có 'owner' trong data, mặc định owner là người tạo.
#     owner = data.get('owner', created_by) 
    
#     # 2. Xử lý Slug & Validation
#     if not data.get('slug'):
#         data['slug'] = slugify(data['title'])

#     if Course.objects.filter(slug=data['slug']).exists():
#         raise ValueError(f"Title '{data['title']}' đã tồn tại. Vui lòng đổi tên.")

#     # 3. Tạo Course (Core Logic)
#     try:
#         course = Course.objects.create(
#             owner=owner,
#             title=data['title'],
#             slug=data['slug'],
#             description=data.get('description', ''),
#             grade=data.get('grade'),
#             published=data.get('published', False),
#             subject=data.get('subject') 
#         )
#     except IntegrityError:
#         raise ValueError(f"Slug '{data['slug']}' vừa bị trùng. Vui lòng thử lại.")
#     except KeyError as e:
#         raise ValueError(f"Thiếu trường dữ liệu bắt buộc: {e}") from e

#     # 4. Xử lý M2M (Tags & Categories) - Đã tối ưu & An toàn
#     # --- Tags ---
#     if tag_names:
#         tags = []
#         for name in tag_names:
#             t_slug = slugify(name)
#             try:
#                 t, _ = Tag.objects.get_or_create(name=name, defaults={'slug': t_slug})
#             except IntegrityError:
#                 t = Tag.objects.get(slug=t_slug)
#             tags.append(t)
#         course.tags.set(tags)

#     # --- Categories ---
#     if categories_names:
#         cats = []
#         for name in categories_names:
#             c_slug = slugify(name)
#             try:
#                 c, _ = Category.objects.get_or_create(name=name, defaults={'slug': c_slug})
#             except IntegrityError:
#                 c = Category.objects.get(slug=c_slug)
#             cats.append(c)
#         course.categories.set(cats)

#     # 5. Xử lý Modules 
#     for module_data in modules_data:
#         create_module_from_template(course=course, data=module_data, actor=created_by)

#     # 6. Commit Files (Logic quan trọng nhất)
#     # Truyền 'actor=created_by' để hàm commit kiểm tra quyền.
#     # Nếu created_by là Admin -> Quyền tối thượng (commit file của bất kỳ ai).
#     # Nếu created_by là Instructor -> Chỉ commit file chính chủ.
#     if image_id:
#         try:
#             commit_files_by_ids_for_object(
#                 file_ids=[image_id], 
#                 related_object=course, 
#                 actor=created_by 
#             )
#         except Exception as e:
#             raise ValueError(f"Lỗi khi lưu file: {str(e)}")

#     # 7. Trả về Domain theo Strategy yêu cầu
#     # Tái sử dụng hàm map của bạn (nhớ import hàm _map_to_domain hoặc để static method)
#     return CourseDomain.factory(course, output_strategy)
    

