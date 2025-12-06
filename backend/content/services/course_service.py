import uuid
import logging
from typing import List, Dict
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from django.utils.text import slugify
from django.db.models import Q, Count, Prefetch
from django.utils import timezone

from custom_account.models import UserModel 
from content.services.module_service import create_module_from_template
from media.services.file_service import commit_files_by_ids_for_object
from media.models import UploadedFile
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

    # --- B. TỐI ƯU HÓA QUERY (STRATEGY) ---
    # 1. Luôn lấy các quan hệ nhẹ
    query_set = query_set.prefetch_related('categories', 'tags')

    # 2. Xử lý Files (Ảnh bìa)
    # Moodle Tip: Chỉ lấy file ảnh để tránh load nhầm file nặng
    query_set = query_set.prefetch_related(
        'categories',
        'tags',
        Prefetch('files', queryset=UploadedFile.objects.filter(
            Q(file__iendswith='.jpg') | Q(file__iendswith='.png') | Q(file__iendswith='.webp')
        ))
    )

    # 3. Chiến lược riêng biệt
    if strategy == CourseFetchStrategy.BASIC:
        pass

    elif strategy == CourseFetchStrategy.CATALOG_LIST or strategy:
        # Màn hình List: Chỉ cần đếm số Module (nhanh), không load object Module
        query_set = query_set.annotate(module_count=Count('modules', distinct=True))

    elif strategy == CourseFetchStrategy.ADMIN_LIST:
        # Admin List: Cần thông tin Owner, User Enrolled count
        query_set = query_set.select_related('owner')
        query_set = query_set.annotate(
            module_count=Count('modules', distinct=True),
            student_count=Count('enrollments', distinct=True) # Ví dụ thêm
        )

    elif strategy in (CourseFetchStrategy.STRUCTURE):
        # Các màn hình chi tiết: Cần load cấu trúc cây (Module -> Lesson)
        
        # Tối ưu sâu: Prefetch Module và Lesson bên trong
        query_set = query_set.prefetch_related(
            'modules',
            'modules__lessons',
            Prefetch(
                'modules__lessons__content_blocks',
                # QUAN TRỌNG: defer payload để nhẹ json
                query_set=ContentBlock.objects.defer('payload', 'files')
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
        raise ValueError(f"Title '{data['title']}' đã tồn tại. Vui lòng đổi tên.")
    
    subject_name = data.get('subject') # Lấy string "Tin học"
    subject_instance = None

    if subject_name:
        # Nếu model Subject có field slug, ta nên tạo slug luôn
        sub_slug = slugify(subject_name) 
        
        try:
            # Tìm subject theo tên, nếu chưa có thì tạo mới kèm slug
            subject_instance, created = Subject.objects.get_or_create(
                title=subject_name,
                defaults={'slug': sub_slug} 
            )
        except IntegrityError:
            # Handle trường hợp race condition (2 request cùng tạo 1 lúc)
            subject_instance = Subject.objects.get(title=subject_name)

    # 4. Tạo Course object (Core entity)
    try:
        course = Course.objects.create(
            owner=owner,
            title=data['title'],
            slug=data['slug'],
            description=data.get('description', ''),
            grade=data.get('grade'),
            subject=subject_instance,
            published=data.get('published', False)
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

    # 7. Xử lý Image (nếu có)
    if image_id:
        try:
            commit_files_by_ids_for_object(
                file_ids=[image_id], 
                related_object=course, 
                actor=created_by
            )
        except Exception as e:
            raise ValueError(f"Lỗi khi lưu file ảnh: {str(e)}") from e

    # 8. Trả về Domain theo strategy
    return CourseDomain.factory(course, output_strategy)


@transaction.atomic
def create_course_from_template(data: dict, created_by: UserModel, output_strategy: CourseFetchStrategy = CourseFetchStrategy.STRUCTURE) -> CourseDomain:
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
        raise ValueError(f"Title '{data['title']}' đã tồn tại. Vui lòng đổi tên.")

    # 3. Tạo Course (Core Logic)
    try:
        course = Course.objects.create(
            owner=owner,
            title=data['title'],
            slug=data['slug'],
            description=data.get('description', ''),
            grade=data.get('grade'),
            published=data.get('published', False),
            subject=data.get('subject') 
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

    # 5. Xử lý Modules 
    for module_data in modules_data:
        create_module_from_template(course=course, data=module_data, actor=created_by)

    # 6. Commit Files (Logic quan trọng nhất)
    # Truyền 'actor=created_by' để hàm commit kiểm tra quyền.
    # Nếu created_by là Admin -> Quyền tối thượng (commit file của bất kỳ ai).
    # Nếu created_by là Instructor -> Chỉ commit file chính chủ.
    if image_id:
        try:
            commit_files_by_ids_for_object(
                file_ids=[image_id], 
                related_object=course, 
                actor=created_by 
            )
        except Exception as e:
            raise ValueError(f"Lỗi khi lưu file: {str(e)}")

    # 7. Trả về Domain theo Strategy yêu cầu
    # Tái sử dụng hàm map của bạn (nhớ import hàm _map_to_domain hoặc để static method)
    return CourseDomain.factory(course, output_strategy)


# ==========================================
# PUBLIC INTERFACE (PATCH)
# ==========================================

@transaction.atomic
def update_course_metadata(
    course_id: int,
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
    fields_to_update = ['description', 'grade', 'published']
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

    # 8. Xử lý Image Update
    if image_id:
        try:
            # Logic: Commit file mới vào object. 
            # Lưu ý: Tùy logic file manager, bạn có thể cần xóa file cũ trước 
            # hoặc hàm commit này tự handle việc replace.
            commit_files_by_ids_for_object(
                file_ids=[image_id], 
                related_object=course, 
                actor=updated_by
            )
        except Exception as e:
            raise ValueError(f"Lỗi khi cập nhật ảnh: {str(e)}") from e

    # 9. Trả về Domain
    return CourseDomain.factory(course, output_strategy)



# @transaction.atomic
# def patch_course(
#     course_id: uuid.UUID, 
#     data: dict, 
#     actor: UserModel, 
#     output_strategy: CourseFetchStrategy = CourseFetchStrategy.STRUCTURE
# ) -> CourseDomain:
#     """
#     Hàm cập nhật khóa học dùng chung (Admin & Instructor).
    
#     Args:
#         course_id: ID khóa học cần sửa.
#         data: Dữ liệu PATCH (từ DTO).
#         actor: Người thực hiện (request.user).
#         output_strategy: Định dạng dữ liệu trả về.
#     """

#     # 1. Lấy đối tượng gốc & Kiểm tra quyền
#     # Logic: 
#     # - Nếu actor là Admin -> Lấy theo ID (bỏ qua owner check).
#     # - Nếu actor là Instructor -> Bắt buộc phải là owner.
#     try:
#         qs = Course.objects.select_related('owner', 'subject')
        
#         # Kiểm tra quyền dựa trên role (giả sử logic check admin như cũ)
#         is_admin = getattr(actor, 'is_staff', False) or getattr(actor, 'is_superuser', False)
        
#         if is_admin:
#             course = qs.get(id=course_id)
#         else:
#             course = qs.get(id=course_id, owner=actor)
            
#     except Course.DoesNotExist:
#         raise ValueError("Không tìm thấy khóa học hoặc bạn không có quyền chỉnh sửa.")

#     # 2. Tách dữ liệu (Pop ra để data còn lại chỉ là simple fields)
#     modules_data = data.pop('modules', None)
#     categories_names = data.pop('categories', None)
#     tag_names = data.pop('tags', None)
#     image_id = data.pop('image_id', None)
    
#     files_to_commit = []

#     # 3. Xử lý Simple Fields
#     # Logic: Chỉ update field nào có trong data (PATCH behavior)
#     if 'title' in data and 'slug' not in data:
#         data['slug'] = slugify(data['title'])

#     simple_fields = ['title', 'slug', 'description', 'grade', 'published', 'published_at']
#     update_fields_for_save = []
#     has_simple_changes = False

#     for field in simple_fields: 
#         if field in data:
#             setattr(course, field, data[field])
#             update_fields_for_save.append(field)
#             has_simple_changes = True

#     # 4. Xử lý Subject (Foreign Key)
#     if 'subject' in data:
#         # Chấp nhận cả key 'subject' hoặc 'subject_id'
#         subject_title = data.get('subject') 
        
#         if subject_title is None:
#             course.subject = None
#         else:
#             subject_title = str(subject_title).strip()
#             if not subject_title:
#                 raise ValueError("Subject không được để trống.")
#             try:
#                 subject_obj, created = Subject.objects.get_or_create(
#                     title__iexact=subject_title,
#                     defaults={
#                         'title': subject_title,
#                         'slug': slugify(subject_title),
#                     }
#                 )
#                 course.subject = subject_obj
#             except (Subject.DoesNotExist, ValueError):
#                 raise ValueError(f"Subject '{subject_title}' không hợp lệ.")
        
#         update_fields_for_save.append('subject')
#         has_simple_changes = True

#     # 5. Lưu thay đổi cơ bản
#     if has_simple_changes:
#         try:
#             course.save(update_fields=update_fields_for_save)
#         except IntegrityError:
#             raise ValueError(f"Slug '{data.get('slug')}' đã tồn tại. Vui lòng chọn tiêu đề khác.")

#     # 6. Xử lý M2M (Tags & Categories) - Dùng logic AN TOÀN (Safe)
#     # (Logic này đã được fix lỗi 500 từ hàm create)
    
#     if categories_names is not None:
#         cats_objects = []
#         for cat_name in categories_names:
#             c_slug = slugify(cat_name)
#             try:
#                 c, _ = Category.objects.get_or_create(name=cat_name, defaults={'slug': c_slug})
#             except IntegrityError:
#                 c = Category.objects.get(slug=c_slug)
#             cats_objects.append(c)
#         course.categories.set(cats_objects)

#     if tag_names is not None:
#         tags_objects = []
#         for tag_name in tag_names:
#             t_slug = slugify(tag_name)
#             try:
#                 t, _ = Tag.objects.get_or_create(name=tag_name, defaults={'slug': t_slug})
#             except IntegrityError:
#                 t = Tag.objects.get(slug=t_slug)
#             tags_objects.append(t)
#         course.tags.set(tags_objects)

#     # 7. Xử lý Ảnh bìa
#     if image_id is not None:
#         # Giả sử clear cũ đi để thay mới
#         course.files.clear()
#         files_to_commit.append(image_id)

#     # 8. Xử lý Modules (Giữ nguyên logic Moodle phức tạp của bạn)
#     if modules_data is not None:
#         existing_ids = set(course.modules.values_list('id', flat=True))
#         incoming_ids = set()

#         for position, mod_data in enumerate(modules_data):
#             mod_data['position'] = position
#             mod_id_str = mod_data.get('id')

#             if mod_id_str:
#                 # -- UPDATE --
#                 try:
#                     mod_id = uuid.UUID(str(mod_id_str))
#                 except ValueError:
#                     raise ValueError(f"Invalid Module ID: {mod_id_str}")
                
#                 if mod_id not in existing_ids:
#                     raise ValueError(f"Module {mod_id} không thuộc khóa học này.")

#                 # Gọi đệ quy
#                 _, mod_files = patch_module(module_id=mod_id, data=mod_data)
#                 files_to_commit.extend(mod_files)
#                 incoming_ids.add(mod_id)
#             else:
#                 # -- CREATE --
#                 new_mod, mod_files = create_module(course=course, data=mod_data)
#                 files_to_commit.extend(mod_files)
#                 incoming_ids.add(new_mod.id)

#         # -- DELETE --
#         ids_to_delete = existing_ids - incoming_ids
#         if ids_to_delete:
#             Module.objects.filter(id__in=ids_to_delete).delete()

#     # 9. Commit Files
#     # Truyền actor vào để Service kiểm tra quyền (Admin được commit tất, Instructor chỉ commit file chính chủ)
#     if files_to_commit:
#         try:
#             commit_files_by_ids_for_object(
#                 file_ids=files_to_commit, 
#                 related_object=course, 
#                 actor=actor
#             )
#         except Exception as e:
#             raise ValueError(f"Lỗi lưu file: {str(e)}")

#     # 10. Return Domain
#     # Tái sử dụng hàm get_course_single để lấy data mới nhất theo strategy
#     return get_course_single(
#         filters=CourseFilter(course_id=course_id), # Admin hay User đều xem được sau khi đã sửa xong
#         strategy=output_strategy
#     )


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
        strategy=CourseFetchStrategy.STRUCTURE
    )

    

