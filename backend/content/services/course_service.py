import uuid
import logging
from typing import Any, Dict, List
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Prefetch
from django.db import IntegrityError
from django.utils.text import slugify
from django.db.models import Q
from django.utils import timezone

from custom_account.models import UserModel 
from media.services import file_service
from media.models import UploadedFile, FileStatus
from content.domains.course_domain import CourseDomain
from content.domains.enrollment_domain import EnrollmentDomain
from content.models import Course, Module, Lesson, Enrollment, Category, Tag, Subject
from content.services import module_service
from core.exceptions import DomainError, CourseNotFoundError
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

    # --- B. TỐI ƯU HÓA QUERY (STRATEGY) ---
    # 1. Luôn lấy các quan hệ nhẹ
    query_set = query_set.prefetch_related('categories', 'tags', 'files')

    # 2. Tùy chọn theo chiến lược
    if strategy == CourseFetchStrategy.OVERVIEW:
        # Chỉ cần metadata, không cần join nặng
        pass 

    elif strategy == CourseFetchStrategy.FULL_STRUCTURE:
        # Cần lấy cả cây bài học (Modules -> Lessons)
        # Dùng cho trang học hoặc trang edit của giáo viên
        query_set = query_set.prefetch_related('modules__lessons')
        # Nếu cần check owner/subject chi tiết thì select thêm
        query_set = query_set.select_related('owner', 'subject')

    elif strategy == CourseFetchStrategy.ADMIN_DETAIL:
        # Admin cần full object của owner và subject
        query_set = query_set.select_related('owner', 'subject')
        query_set = query_set.prefetch_related('modules__lessons')

    # Mặc định sort
    return query_set.order_by('-created_at')


def _map_to_domain(instance, strategy: CourseFetchStrategy) -> CourseDomain:
    """
    Hàm nội bộ: Chọn Factory Method phù hợp của Domain.
    """
    if strategy == CourseFetchStrategy.ADMIN_DETAIL:
        return CourseDomain.from_model_admin(instance)
    elif strategy == CourseFetchStrategy.FULL_STRUCTURE:
        return CourseDomain.from_model(instance) # Hàm này load full modules
    else:
        return CourseDomain.from_model_overview(instance) # Hàm nhẹ


# ==========================================
# PUBLIC INTERFACE (GET)
# ==========================================

logger = logging.getLogger(__name__)

def get_courses(filters: CourseFilter, strategy: CourseFetchStrategy = CourseFetchStrategy.OVERVIEW) -> List[CourseDomain]:
    """
    Lấy danh sách khóa học (List).
    Không bao giờ raise lỗi Not Found, chỉ trả về list rỗng.
    """
    try:
        query_set = _build_queryset(filters, strategy)
        return [_map_to_domain(course, strategy) for course in query_set]
    except Exception as e:
        logger.error(f"Error listing courses: {e}", exc_info=True)
        raise DomainError("Lỗi hệ thống khi lấy danh sách khóa học.")


def get_course_single(filters: CourseFilter, strategy: CourseFetchStrategy = CourseFetchStrategy.FULL_STRUCTURE) -> CourseDomain:
    """
    Lấy chi tiết 1 khóa học (Detail).
    Raise DomainError nếu không tìm thấy (hoặc không thỏa mãn filter).
    """
    try:
        query_set = _build_queryset(filters, strategy)
        course = query_set.get() # Sẽ raise DoesNotExist hoặc MultipleObjectsReturned
        return _map_to_domain(course, strategy)
    
    except Course.DoesNotExist:
        # Context hóa lỗi: Nếu filter có owner -> User ko có quyền hoặc ID sai
        if filters.owner:
            raise DomainError("Không tìm thấy khóa học hoặc bạn không có quyền truy cập.")
        if filters.enrolled_user:
            raise DomainError("Bạn chưa ghi danh vào khóa học này.")
        raise DomainError("Không tìm thấy khóa học.")
        
    except Exception as e:
        logger.error(f"Error getting course detail: {e}", exc_info=True)
        raise DomainError("Lỗi hệ thống khi lấy thông tin khóa học.")
    

# ==========================================
# PUBLIC INTERFACE (CREATE)
# ==========================================

@transaction.atomic
def create_course(data: dict, created_by: UserModel, output_strategy: CourseFetchStrategy = CourseFetchStrategy.OVERVIEW) -> CourseDomain:
    """
    Hàm tạo khóa học dùng chung cho cả Admin và Instructor.
    
    Args:
        data: Dữ liệu đầu vào (dict từ DTO).
        created_by: User thực hiện hành động này (request.user).
        output_strategy: Muốn trả về Domain kiểu gì (Overview hay Admin Detail).
    """
    
    # 1. Chuẩn bị dữ liệu (Tách nested data)
    modules_data = data.get('modules', [])
    categories_names = data.get('categories', [])
    tag_names = data.get('tags', [])
    image_id = data.get('image_id')

    # Logic: Nếu là Admin tạo hộ, 'owner' trong data có thể khác 'created_by'.
    # Nếu không có 'owner' trong data, mặc định owner là người tạo.
    owner = data.get('owner', created_by) 
    
    # 2. Xử lý Slug & Validation
    if not data.get('slug'):
        data['slug'] = slugify(data['title'])

    if Course.objects.filter(slug=data['slug']).exists():
        raise ValueError(f"Slug '{data['slug']}' đã tồn tại. Vui lòng đổi tên.")

    # 3. Tạo Course (Core Logic)
    try:
        course = Course.objects.create(
            owner=owner,
            title=data['title'],
            slug=data['slug'],
            description=data.get('description', ''),
            grade=data.get('grade'),
            published=data.get('published', False),
            subject=data.get('subject') # Giả sử subject đã được validate/lấy object ở view hoặc serializer
        )
    except IntegrityError:
        raise ValueError(f"Slug '{data['slug']}' vừa bị trùng. Vui lòng thử lại.")
    except KeyError as e:
        raise ValueError(f"Thiếu trường dữ liệu bắt buộc: {e}") from e

    # 4. Xử lý M2M (Tags & Categories) - Đã tối ưu & An toàn
    # --- Tags ---
    if tag_names:
        tags = []
        for name in tag_names:
            t_slug = slugify(name)
            try:
                t, _ = Tag.objects.get_or_create(name=name, defaults={'slug': t_slug})
            except IntegrityError:
                t = Tag.objects.get(slug=t_slug)
            tags.append(t)
        course.tags.set(tags)

    # --- Categories ---
    if categories_names:
        cats = []
        for name in categories_names:
            c_slug = slugify(name)
            try:
                c, _ = Category.objects.get_or_create(name=name, defaults={'slug': c_slug})
            except IntegrityError:
                c = Category.objects.get(slug=c_slug)
            cats.append(c)
        course.categories.set(cats)

    # 5. Xử lý Modules & Files
    files_to_commit = [image_id] if image_id else []
    
    for module_data in modules_data:
        _, mod_files = module_service.create_module(course=course, data=module_data)
        if mod_files:
            files_to_commit.extend(mod_files)

    # 6. Commit Files (Logic quan trọng nhất)
    # Truyền 'actor=created_by' để hàm commit kiểm tra quyền.
    # Nếu created_by là Admin -> Quyền tối thượng (commit file của bất kỳ ai).
    # Nếu created_by là Instructor -> Chỉ commit file chính chủ.
    if files_to_commit:
        try:
            file_service.commit_files_by_ids_for_object(
                file_ids=files_to_commit, 
                related_object=course, 
                actor=created_by 
            )
        except Exception as e:
            raise ValueError(f"Lỗi khi lưu file: {str(e)}")

    # 7. Trả về Domain theo Strategy yêu cầu
    # Tái sử dụng hàm map của bạn (nhớ import hàm _map_to_domain hoặc để static method)
    return _map_to_domain(course, output_strategy)


# ==========================================
# PUBLIC INTERFACE (PATCH)
# ==========================================

@transaction.atomic
def patch_course(
    course_id: uuid.UUID, 
    data: dict, 
    actor: UserModel, 
    output_strategy: CourseFetchStrategy = CourseFetchStrategy.FULL_STRUCTURE
) -> CourseDomain:
    """
    Hàm cập nhật khóa học dùng chung (Admin & Instructor).
    
    Args:
        course_id: ID khóa học cần sửa.
        data: Dữ liệu PATCH (từ DTO).
        actor: Người thực hiện (request.user).
        output_strategy: Định dạng dữ liệu trả về.
    """

    # 1. Lấy đối tượng gốc & Kiểm tra quyền
    # Logic: 
    # - Nếu actor là Admin -> Lấy theo ID (bỏ qua owner check).
    # - Nếu actor là Instructor -> Bắt buộc phải là owner.
    try:
        qs = Course.objects.select_related('owner', 'subject')
        
        # Kiểm tra quyền dựa trên role (giả sử logic check admin như cũ)
        is_admin = getattr(actor, 'is_staff', False) or getattr(actor, 'is_superuser', False)
        
        if is_admin:
            course = qs.get(id=course_id)
        else:
            course = qs.get(id=course_id, owner=actor)
            
    except Course.DoesNotExist:
        raise ValueError("Không tìm thấy khóa học hoặc bạn không có quyền chỉnh sửa.")

    # 2. Tách dữ liệu (Pop ra để data còn lại chỉ là simple fields)
    modules_data = data.pop('modules', None)
    categories_names = data.pop('categories', None)
    tag_names = data.pop('tags', None)
    image_id = data.pop('image_id', None)
    
    files_to_commit = []

    # 3. Xử lý Simple Fields
    # Logic: Chỉ update field nào có trong data (PATCH behavior)
    if 'title' in data and 'slug' not in data:
        data['slug'] = slugify(data['title'])

    simple_fields = ['title', 'slug', 'description', 'grade', 'published', 'published_at']
    update_fields_for_save = []
    has_simple_changes = False

    for field in simple_fields:
        if field in data:
            setattr(course, field, data[field])
            update_fields_for_save.append(field)
            has_simple_changes = True

    # 4. Xử lý Subject (Foreign Key)
    if 'subject' in data or 'subject_id' in data:
        # Chấp nhận cả key 'subject' hoặc 'subject_id'
        sid = data.get('subject') or data.get('subject_id')
        
        if sid is None:
            course.subject = None
        else:
            try:
                course.subject = Subject.objects.get(id=sid)
            except (Subject.DoesNotExist, ValueError):
                raise ValueError(f"Subject ID '{sid}' không hợp lệ.")
        
        update_fields_for_save.append('subject')
        has_simple_changes = True

    # 5. Lưu thay đổi cơ bản
    if has_simple_changes:
        try:
            course.save(update_fields=update_fields_for_save)
        except IntegrityError:
            raise ValueError(f"Slug '{data.get('slug')}' đã tồn tại. Vui lòng chọn tiêu đề khác.")

    # 6. Xử lý M2M (Tags & Categories) - Dùng logic AN TOÀN (Safe)
    # (Logic này đã được fix lỗi 500 từ hàm create)
    
    if categories_names is not None:
        cats_objects = []
        for cat_name in categories_names:
            c_slug = slugify(cat_name)
            try:
                c, _ = Category.objects.get_or_create(name=cat_name, defaults={'slug': c_slug})
            except IntegrityError:
                c = Category.objects.get(slug=c_slug)
            cats_objects.append(c)
        course.categories.set(cats_objects)

    if tag_names is not None:
        tags_objects = []
        for tag_name in tag_names:
            t_slug = slugify(tag_name)
            try:
                t, _ = Tag.objects.get_or_create(name=tag_name, defaults={'slug': t_slug})
            except IntegrityError:
                t = Tag.objects.get(slug=t_slug)
            tags_objects.append(t)
        course.tags.set(tags_objects)

    # 7. Xử lý Ảnh bìa
    if image_id is not None:
        # Giả sử clear cũ đi để thay mới
        course.files.clear()
        files_to_commit.append(image_id)

    # 8. Xử lý Modules (Giữ nguyên logic Moodle phức tạp của bạn)
    if modules_data is not None:
        existing_ids = set(course.modules.values_list('id', flat=True))
        incoming_ids = set()

        for position, mod_data in enumerate(modules_data):
            mod_data['position'] = position
            mod_id_str = mod_data.get('id')

            if mod_id_str:
                # -- UPDATE --
                try:
                    mod_id = uuid.UUID(str(mod_id_str))
                except ValueError:
                    raise ValueError(f"Invalid Module ID: {mod_id_str}")
                
                if mod_id not in existing_ids:
                    raise ValueError(f"Module {mod_id} không thuộc khóa học này.")

                # Gọi đệ quy
                _, mod_files = module_service.patch_module(module_id=mod_id, data=mod_data)
                files_to_commit.extend(mod_files)
                incoming_ids.add(mod_id)
            else:
                # -- CREATE --
                new_mod, mod_files = module_service.create_module(course=course, data=mod_data)
                files_to_commit.extend(mod_files)
                incoming_ids.add(new_mod.id)

        # -- DELETE --
        ids_to_delete = existing_ids - incoming_ids
        if ids_to_delete:
            Module.objects.filter(id__in=ids_to_delete).delete()

    # 9. Commit Files
    # Truyền actor vào để Service kiểm tra quyền (Admin được commit tất, Instructor chỉ commit file chính chủ)
    if files_to_commit:
        try:
            file_service.commit_files_by_ids_for_object(
                file_ids=files_to_commit, 
                related_object=course, 
                actor=actor
            )
        except Exception as e:
            raise ValueError(f"Lỗi lưu file: {str(e)}")

    # 10. Return Domain
    # Tái sử dụng hàm get_course_single để lấy data mới nhất theo strategy
    return get_course_single(
        filters=CourseFilter(course_id=course_id), # Admin hay User đều xem được sau khi đã sửa xong
        strategy=output_strategy
    )


# ==========================================
# PUBLIC INTERFACE (DELETE)
# ==========================================

@transaction.atomic
def delete_course(course_id: uuid.UUID, actor: UserModel) -> None:
    """
    Xóa khóa học và QUÉT SẠCH tất cả file liên quan (kể cả trong bài học con).
    Dùng chung cho Admin và Instructor.
    
    Args:
        course_id: ID khóa học cần xóa.
        actor: Người thực hiện hành động (request.user).
    """
    
    # 1. Tìm và xác thực quyền (Authorization)
    try:
        # Kiểm tra xem actor có phải Admin không
        is_admin = getattr(actor, 'is_staff', False) or getattr(actor, 'is_superuser', False)
        
        if is_admin:
            # Admin: Xóa không cần check owner
            course = Course.objects.prefetch_related('modules__lessons').get(pk=course_id)
        else:
            # Instructor: Phải là owner mới được xóa
            course = Course.objects.prefetch_related('modules__lessons').get(pk=course_id, owner=actor)
            
    except Course.DoesNotExist:
        raise DomainError("Không tìm thấy khóa học hoặc bạn không có quyền xóa.")

    # 2. THU THẬP ID CỦA TẤT CẢ ĐỐI TƯỢNG LIÊN QUAN
    # Để xóa file, ta cần biết ID của Course, tất cả Modules, và tất cả Lessons
    target_objects = {
        ContentType.objects.get_for_model(Course): [course.pk],
    }

    # Lấy ID của Modules
    module_ids = [m.pk for m in course.modules.all()]
    if module_ids:
        target_objects[ContentType.objects.get_for_model(Module)] = module_ids

    # Lấy ID của Lessons (Duyệt qua các module)
    lesson_ids = []
    for module in course.modules.all():
        lesson_ids.extend([l.pk for l in module.lessons.all()])
    
    if lesson_ids:
        target_objects[ContentType.objects.get_for_model(Lesson)] = lesson_ids

    # 3. TRUY VẤN VÀ XÓA UPLOADEDFILE
    # Xây dựng query Q object động
    files_filter = Q()
    for c_type, ids in target_objects.items():
        files_filter |= Q(content_type=c_type, object_id__in=ids)

    # Thực hiện xóa
    if files_filter:
        # Tìm các file liên quan
        files_to_delete = UploadedFile.objects.filter(files_filter)
        count = files_to_delete.count()
        
        # GỌI DELETE() TRÊN QUERYSET
        # Nhờ Signal ở Bước 1, việc này sẽ:
        # a. Xóa record trong DB
        # b. Kích hoạt signal -> Xóa file trên S3
        files_to_delete.delete()
        
        logger.info(f"Đã dọn dẹp {count} file đính kèm trong Course {course_id} và các bài học con.")

    # 4. Cuối cùng mới xóa Course (Cascade sẽ xóa Module/Lesson trong DB)
    course.delete()
    
    return None


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
        qs = Course.objects.all()
        is_admin = getattr(actor, 'is_staff', False) or getattr(actor, 'is_superuser', False)

        if is_admin:
            course = qs.get(pk=course_id)
        else:
            course = qs.get(pk=course_id, owner=actor)
            
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
        strategy=CourseFetchStrategy.OVERVIEW 
    )

    

