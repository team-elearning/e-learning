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
from media.models import UploadedFile, FileStatus
from content.domains.course_domain import CourseDomain
from content.domains.enrollment_domain import EnrollmentDomain
from content.models import Course, Module, Lesson, Enrollment, Category, Tag, Subject
from content.services import module_service
from content.services.exceptions import DomainError, CourseNotFoundError, NotFoundError, InvalidOperation



def list_courses() -> List[CourseDomain]:
    """
    CHỈ lấy metadata của course (và các quan hệ nhẹ).
    KHÔNG lấy modules/lessons.
    """
    
    # Sử dụng prefetch_related để tối ưu M2M, tránh N+1 queries
    course_models = Course.objects.filter(published=True).prefetch_related(
        'categories', 'tags', 'files'
    ).order_by('title')
    
    course_domains = [CourseDomain.from_model_overview(course) for course in course_models]
    return course_domains


def list_enrolled_courses_for_user(user: UserModel) -> List[CourseDomain]: 
        """
        Lấy tất cả các Course mà một user đã ghi danh.
        """
        try:
            # Lọc Course, đi ngược qua 'enrollments' (related_name)
            # để tìm các bản ghi có 'user' là user hiện tại.
            enrolled_courses = Course.objects.filter(
                enrollments__user=user
            ).select_related(
                'owner', 'subject' # Tối ưu hóa query
            ).prefetch_related(
                'categories', 'tags'
            ).distinct().order_by('title')
            
            # Convert các model Django sang DTO (Domain)
            return [CourseDomain.from_model(course) for course in enrolled_courses]
            
        except Exception as e:
            logger.error(f"Lỗi service list_enrolled_courses: {e}", exc_info=True)
            raise DomainError("Không thể lấy danh sách khóa học đã ghi danh.")


def get_enrolled_course_detail_for_user(course_id: uuid.UUID, user: UserModel) -> CourseDomain: 
    """
    Lấy chi tiết một course, NHƯNG chỉ khi user đã ghi danh.
    """
    try:
        # Query này sẽ chỉ thành công nếu CẢ 2 điều kiện đều đúng:
        # 1. Course ID tồn tại.
        # 2. Có một bản ghi "enrollments" nối tới user này.
        course = Course.objects.select_related(
            'owner', 'subject'
        ).prefetch_related(
            'categories', 'tags', 'modules__lessons' # (Tối ưu nếu cần)
        ).get(
            pk=course_id,
            enrollments__user=user
        )
        
        return CourseDomain.from_model(course)
        
    except ObjectDoesNotExist:
        # Lỗi này có nghĩa là "Không tìm thấy" HOẶC "Chưa ghi danh"
        raise CourseNotFoundError("Không tìm thấy khóa học hoặc bạn chưa ghi danh vào khóa học này.")
    except Exception as e:
        logger.error(f"Lỗi service get_enrolled_course_detail: {e}", exc_info=True)
        raise DomainError(f"Lỗi khi lấy khóa học: {e}")
        

def get_course_by_id(course_id: uuid.UUID) -> CourseDomain:
    """Lấy một course theo ID."""
    try:
        # Tối ưu query bằng select_related và prefetch_related
        course = Course.objects.select_related(
            'owner', 'subject'
        ).prefetch_related(
            'categories', 'tags', 'files', 'modules__lessons'
        ).get(pk=course_id)
        
        return CourseDomain.from_model(course)
        
    except ObjectDoesNotExist:
        raise CourseNotFoundError("Không tìm thấy khóa học.")
    except Exception as e:
        raise DomainError(f"Lỗi khi lấy khóa học: {e}")


def get_course_detail_admin(course_id: uuid.UUID) -> CourseDomain:
    """Lấy một course theo ID."""
    try:
        # Tối ưu query bằng select_related và prefetch_related
        course = Course.objects.select_related(
            'owner', 'subject'
        ).prefetch_related(
            'categories', 'tags', 'files', 'modules__lessons'
        ).get(pk=course_id)
        
        return CourseDomain.from_model_admin(course)
        
    except ObjectDoesNotExist:
        raise CourseNotFoundError("Không tìm thấy khóa học.")
    except Exception as e:
        raise DomainError(f"Lỗi khi lấy khóa học: {e}")


def enroll_user_in_course(course_id: uuid.UUID, user: UserModel) -> EnrollmentDomain:
        """
        Ghi danh một user vào một khóa học.
        
        Điều kiện (theo logic LMS chuẩn):
        1. Khóa học phải tồn tại VÀ đã `published`.
        2. User không phải là `owner` của khóa học.
        3. User chưa ghi danh trước đó.
        """
        try:
            # 1. Tìm khóa học (chỉ khóa đã published)
            course = Course.objects.get(id=course_id, published=True)
        except Course.DoesNotExist:
            raise DomainError("Không tìm thấy khóa học hoặc khóa học chưa được xuất bản.")

        # 2. Check quyền: Owner không thể tự enroll
        if course.owner == user:
            raise DomainError("Bạn không thể tự ghi danh vào khóa học của chính mình.")

        # 3. Tạo enrollment
        try:
            # Dùng get_or_create để tận dụng unique_together
            enrollment, created = Enrollment.objects.get_or_create(
                user=user,
                course=course
            )
            
            if not created:
                raise DomainError("Bạn đã ghi danh vào khóa học này rồi.")
                
            return EnrollmentDomain.from_model(enrollment)
            
        except IntegrityError:
            # Bắt lỗi kép (dù get_or_create thường đã xử lý)
            raise DomainError("Bạn đã ghi danh vào khóa học này rồi.")


def unenroll_user_from_course(course_id: uuid.UUID, user: UserModel) -> None:
        """
        Hủy ghi danh một user khỏi khóa học.
        
        Điều kiện:
        1. Phải tìm thấy record Enrollment của user này trong course này.
        """
        try:
            # 1. Tìm đúng enrollment record
            enrollment = Enrollment.objects.get(
                user=user,
                course_id=course_id
            )
        except Enrollment.DoesNotExist:
            # Nếu không tìm thấy -> Lỗi nghiệp vụ
            raise DomainError("Bạn chưa ghi danh vào khóa học này.")
            
        # 2. Xóa
        enrollment.delete()
        return # Không cần trả về gì


@transaction.atomic
def create_course(data: dict, owner) -> CourseDomain:
    """
    Hàm ĐIỀU PHỐI. Quản lý transaction cho toàn bộ quá trình.
    """
    # 1. Tách dữ liệu lồng nhau và M2M ra khỏi data chính
    modules_data = data.get('modules', [])
    categories_names = data.get('categories', [])
    tag_names = data.get('tags', [])
    image_id = data.get('image_id', None)
    
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
        
            subject=data.get('subject')

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
    if image_id:
        files_to_commit.append(image_id)

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
        file_service.commit_files_by_ids_for_object(files_to_commit, course)
    except Exception as e:
        # Nếu commit file lỗi, chúng ta cần chủ động rollback DB
        # Bằng cách raise một Exception để @transaction.atomic bắt được
        raise ValueError(f"Lỗi khi commit file: {str(e)}")

    return CourseDomain.from_model_overview_admin(course)


@transaction.atomic
def patch_course_instructor(course_id: uuid.UUID, data: dict, owner) -> CourseDomain:
    """
    Hàm ĐIỀU PHỐI (Theo logic Moodle - Granular PATCH).
    Quản lý transaction cho toàn bộ quá trình.
    """
    
    # 1. Lấy đối tượng gốc và kiểm tra quyền
    try:
        course = Course.objects.select_related('owner', 'subject').get(
            id=course_id, 
            owner=owner
        )
    except Course.DoesNotExist:
        raise ValueError(f"Course with id {course_id} not found or you do not have permission.")

    # 2. Tách dữ liệu lồng nhau và M2M
    modules_data = data.pop('modules', None)
    categories_names = data.pop('categories', None)
    tag_names = data.pop('tags', None)
    image_id = data.pop('image_id', None)
    
    files_to_commit = []
    
    # 3. Xử lý các trường đơn giản (Simple fields)
    # (Logic này giống hệt phiên bản trước)
    
    if 'title' in data and 'slug' not in data:
        data['slug'] = slugify(data['title'])

    simple_fields = [
        'title', 'slug', 'description', 
        'grade', 'published', 'published_at'
    ]
    update_fields_for_save = []
    has_simple_changes = False

    for field in simple_fields:
        if field in data:
            setattr(course, field, data[field])
            update_fields_for_save.append(field)
            has_simple_changes = True

    # 4. Xử lý Foreign Keys (ví dụ: Subject)
    # (Logic này giống hệt phiên bản trước)
    if 'subject' in data:
        subject_id = data.get('subject') # Dùng get() để cho phép gán None
        if subject_id is None:
            course.subject = None
        else:
            try:
                # API có thể gửi ID (dạng string/UUID) hoặc object (nếu dùng DTO)
                # Giả sử API gửi ID (giống hàm create)
                subject_id_uuid = uuid.UUID(str(subject_id))
                course.subject = Subject.objects.get(id=subject_id_uuid)
            except (Subject.DoesNotExist, TypeError, ValueError):
                raise ValueError(f"Subject with id '{subject_id}' not found.")
        
        update_fields_for_save.append('subject')
        has_simple_changes = True

    # 5. Lưu các thay đổi (trường đơn giản & FK)
    if has_simple_changes:
        try:
            course.save(update_fields=update_fields_for_save)
        except IntegrityError as e:
            raise ValueError(f"Slug '{data['slug']}' đã tồn tại.")
    
    # 6. Xử lý M2M (Category & Tag) - Logic "Thay thế" (Replace)
    # (Logic này giống hệt phiên bản trước)
    
    if categories_names is not None:
        course.categories.clear()
        for cat_name in categories_names:
            category, _ = Category.objects.get_or_create(
                name=cat_name, 
                defaults={'slug': slugify(cat_name)}
            )
            course.categories.add(category)

    if tag_names is not None:
        course.tags.clear()
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(
                name=tag_name, 
                defaults={'slug': slugify(tag_name)}
            )
            course.tags.add(tag)
            
    # 7. Xử lý Ảnh bìa (File) - Logic "Thay thế"
    # (Logic này giống hệt phiên bản trước)
    if image_id is not None:
        course.files.clear() 
        files_to_commit.append(image_id)

    # 8. Xử lý Modules lồng nhau (LOGIC MOODLE)
    if modules_data is not None:
        
        # Lấy ID các module hiện tại trong DB
        existing_module_ids = set(
            course.modules.values_list('id', flat=True)
        )
        
        # ID các module từ request gửi lên
        incoming_module_ids = set()
        
        # 1. Xử lý Cập nhật (Update) và Tạo mới (Create)
        for position, module_data in enumerate(modules_data):
            module_id_str = module_data.get('id')
            
            # Gán vị trí mới
            module_data['position'] = position 

            if module_id_str:
                # --- UPDATE (PATCH) ---
                try:
                    module_id = uuid.UUID(str(module_id_str))
                except ValueError:
                    raise ValueError(f"Invalid Module ID format: {module_id_str}")

                if module_id not in existing_module_ids:
                    raise ValueError(f"Module {module_id} does not belong to this course.")
                
                # Ủy quyền cho module_service.patch_module
                # (Hàm này bạn sẽ cần tạo, nó cũng phải xử lý lessons bên trong)
                updated_module, module_files = module_service.patch_module(
                    module_id=module_id,
                    data=module_data
                )
                files_to_commit.extend(module_files)
                incoming_module_ids.add(module_id)
                
            else:
                # --- CREATE ---
                # Ủy quyền cho module_service.create_module
                new_module, module_files = module_service.create_module(
                    course=course, 
                    data=module_data
                )
                files_to_commit.extend(module_files)
                # new_module ở đây là Model, nên chúng ta lấy .id
                incoming_module_ids.add(new_module.id)

        # 2. Xử lý Xóa (Delete)
        # Module nào có trong DB mà không có trong request thì XÓA
        ids_to_delete = existing_module_ids - incoming_module_ids
        if ids_to_delete:
            # .delete() sẽ tự động kích hoạt cascade, xóa lessons, v.v.
            Module.objects.filter(id__in=ids_to_delete).delete()

    # 9. (Rất quan trọng) Commit file MỚI
    if files_to_commit:
        try:
            file_service.commit_files_by_ids_for_object(files_to_commit, course)
        except Exception as e:
            raise ValueError(f"Lỗi khi commit file: {str(e)}")

    # 10. Trả về Domain
    # Tải lại toàn bộ để đảm bảo data là mới nhất
    # (Vì chúng ta đã prefetch 'owner' và 'subject' ở Bước 1)
    course_domain = get_course_instructor(owner=owner, course_id=course_id)
    
    return course_domain


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


@transaction.atomic
def patch_course_admin(course_id: uuid.UUID, data: dict) -> CourseDomain:
    """
    Hàm ĐIỀU PHỐI (Theo logic Moodle - Granular PATCH).
    Quản lý transaction cho toàn bộ quá trình.
    """
    
    # 1. Lấy đối tượng gốc 
    try:
        course = Course.objects.select_related('owner', 'subject').get(id=course_id)
    except Course.DoesNotExist:
        raise ValueError(f"Course with id {course_id} not found.")

    # 2. Tách dữ liệu lồng nhau và M2M
    modules_data = data.pop('modules', None)
    categories_names = data.pop('categories', None)
    tag_names = data.pop('tags', None)
    image_id = data.pop('image_id', None)
    
    files_to_commit = []
    
    # 3. Xử lý các trường đơn giản (Simple fields)
    # (Logic này giống hệt phiên bản trước)
    
    if 'title' in data and 'slug' not in data:
        data['slug'] = slugify(data['title'])

    simple_fields = [
        'title', 'slug', 'description', 
        'grade', 'published', 'published_at'
    ]
    update_fields_for_save = []
    has_simple_changes = False

    for field in simple_fields:
        if field in data:
            setattr(course, field, data[field])
            update_fields_for_save.append(field)
            has_simple_changes = True

    # 4. Xử lý Foreign Keys (ví dụ: Subject)
    # (Logic này giống hệt phiên bản trước)
    if 'subject' in data:
        subject_id = data.get('subject') # Dùng get() để cho phép gán None
        if subject_id is None:
            course.subject = None
        else:
            try:
                # API có thể gửi ID (dạng string/UUID) hoặc object (nếu dùng DTO)
                # Giả sử API gửi ID (giống hàm create)
                subject_id_uuid = uuid.UUID(str(subject_id))
                course.subject = Subject.objects.get(id=subject_id_uuid)
            except (Subject.DoesNotExist, TypeError, ValueError):
                raise ValueError(f"Subject with id '{subject_id}' not found.")
        
        update_fields_for_save.append('subject')
        has_simple_changes = True

    # 5. Lưu các thay đổi (trường đơn giản & FK)
    if has_simple_changes:
        try:
            course.save(update_fields=update_fields_for_save)
        except IntegrityError as e:
            raise ValueError(f"Slug '{data['slug']}' đã tồn tại.")
    
    # 6. Xử lý M2M (Category & Tag) - Logic "Thay thế" (Replace)
    # (Logic này giống hệt phiên bản trước)
    
    if categories_names is not None:
        course.categories.clear()
        for cat_name in categories_names:
            category, _ = Category.objects.get_or_create(
                name=cat_name, 
                defaults={'slug': slugify(cat_name)}
            )
            course.categories.add(category)

    if tag_names is not None:
        course.tags.clear()
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(
                name=tag_name, 
                defaults={'slug': slugify(tag_name)}
            )
            course.tags.add(tag)
            
    # 7. Xử lý Ảnh bìa (File) - Logic "Thay thế"
    # (Logic này giống hệt phiên bản trước)
    if image_id is not None:
        course.files.clear() 
        files_to_commit.append(image_id)

    # 8. Xử lý Modules lồng nhau (LOGIC MOODLE)
    if modules_data is not None:
        
        # Lấy ID các module hiện tại trong DB
        existing_module_ids = set(
            course.modules.values_list('id', flat=True)
        )
        
        # ID các module từ request gửi lên
        incoming_module_ids = set()
        
        # 1. Xử lý Cập nhật (Update) và Tạo mới (Create)
        for position, module_data in enumerate(modules_data):
            module_id_str = module_data.get('id')
            
            # Gán vị trí mới
            module_data['position'] = position 

            if module_id_str:
                # --- UPDATE (PATCH) ---
                try:
                    module_id = uuid.UUID(str(module_id_str))
                    module_title = module_data.get('title')
                except ValueError:
                    raise ValueError(f"Invalid Module ID format: {module_id_str}")

                if module_id not in existing_module_ids:
                    raise ValueError(f"Module {module_title} does not belong to this course.")
                
                # Ủy quyền cho module_service.patch_module
                # (Hàm này bạn sẽ cần tạo, nó cũng phải xử lý lessons bên trong)
                updated_module, module_files = module_service.patch_module(
                    module_id=module_id,
                    data=module_data
                )
                files_to_commit.extend(module_files)
                incoming_module_ids.add(module_id)
                
            else:
                # --- CREATE ---
                # Ủy quyền cho module_service.create_module
                new_module, module_files = module_service.create_module(
                    course=course, 
                    data=module_data
                )
                files_to_commit.extend(module_files)
                # new_module ở đây là Model, nên chúng ta lấy .id
                incoming_module_ids.add(new_module.id)

        # 2. Xử lý Xóa (Delete)
        # Module nào có trong DB mà không có trong request thì XÓA
        ids_to_delete = existing_module_ids - incoming_module_ids
        if ids_to_delete:
            # .delete() sẽ tự động kích hoạt cascade, xóa lessons, v.v.
            Module.objects.filter(id__in=ids_to_delete).delete()

    # 9. (Rất quan trọng) Commit file MỚI
    if files_to_commit:
        try:
            file_service.commit_files_by_ids_for_object(files_to_commit, course)
        except Exception as e:
            raise ValueError(f"Lỗi khi commit file: {str(e)}")

    # 10. Trả về Domain
    # Tải lại toàn bộ để đảm bảo data là mới nhất
    # (Vì chúng ta đã prefetch 'owner' và 'subject' ở Bước 1)
    course_domain = get_course_detail_admin(course_id=course_id)
    
    return course_domain


logger = logging.getLogger(__name__)
@transaction.atomic
def delete_course_by_id(course_id: uuid.UUID) -> None:
    """
    Xóa một khóa học và dọn dẹp TẤT CẢ các file liên quan.
    Chỉ owner (Instructor) mới được xóa.
    """
    
    # 1. Tìm và xác thực course (giống hàm delete của bạn)
    try:
        course = Course.objects.get(pk=course_id)
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


# @transaction.atomic
# def publish_course(course_id: str, publish_data: Any) -> CourseDomain:
#     """
#     Publish một course. Áp dụng các quy tắc nghiệp vụ trong Domain.
#     """
#     # 1. Lấy Aggregate Root (đã bao gồm tất cả modules/lessons)
#     course_domain = get_course(course_id)
    
#     # 2. Lấy cờ (flag) từ command (view của bạn truyền vào)
#     require_all = getattr(publish_data, 'require_all_lessons_published', False)
    
#     # 3. Gọi logic nghiệp vụ (Domain)
#     # Hàm này sẽ ném ra InvalidOperation nếu quy tắc 'can_publish' thất bại
#     try:
#         course_domain.publish(require_all_lessons_published=require_all)
#     except InvalidOperation as e:
#         # Re-raise lỗi nghiệp vụ để view xử lý (HTTP 400)
#         raise e
    
#     # 4. Lưu trạng thái mới vào DB (Repository Save)
#     try:
#         # Lấy model instance để lưu
#         course_model = Course.objects.get(id=course_id)
        
#         # Đồng bộ trạng thái từ domain (đã được sửa)
#         course_model.published = course_domain.published
#         course_model.published_at = course_domain.published_at # Đây là datetime

#         course_model.save(update_fields=['published', 'published_at'])
        
#         return course_domain
        
#     except Course.DoesNotExist:
#         raise NotFoundError("Không tìm thấy khóa học để lưu.")
#     except Exception as e:
#         raise DomainError(f"Lỗi khi lưu trạng thái publish: {e}")


# @transaction.atomic
# def unpublish_course(course_id: str) -> CourseDomain:
#     """
#     Unpublish một course.
#     """
#     # 1. Lấy Aggregate Root
#     course_domain = get_course(course_id)
    
#     # 2. Gọi logic nghiệp vụ (Domain)
#     course_domain.unpublish() # Hàm này sẽ set published=False, published_at=None
    
#     # 3. Lưu trạng thái mới vào DB (Repository Save)
#     try:
#         course_model = Course.objects.get(id=course_id)
        
#         # Đồng bộ trạng thái từ domain
#         course_model.published = course_domain.published
#         course_model.published_at = course_domain.published_at # Đây là None

#         course_model.save(update_fields=['published', 'published_at'])
        
#         # View của bạn kiểm tra 'if not updated:',
#         # nên chúng ta trả về domain object
#         return course_domain
        
#     except Course.DoesNotExist:
#         raise NotFoundError("Không tìm thấy khóa học để lưu.")
#     except Exception as e:
#         raise DomainError(f"Lỗi khi lưu trạng thái unpublish: {e}")


def list_course_overviews_instructor(owner: UserModel) -> List[CourseDomain]:
    """
    CHỈ lấy metadata của course (và các quan hệ nhẹ).
    KHÔNG lấy modules/lessons.
    """
    # prefetch_related chỉ lấy categories và tags
    course_models = Course.objects.filter(owner=owner).prefetch_related(
        'categories', 'tags', 'files'
    ).order_by('title')
    
    # Hàm from_model này KHÔNG NÊN load modules/lessons
    # Nếu nó đang load, bạn cần tạo một hàm from_model_overview() khác
    course_domains = [CourseDomain.from_model_overview(course) for course in course_models]
    return course_domains


def list_all_course_overviews() -> List[CourseDomain]:
    """
    Lấy danh sách cho Admin, trả về Domain chứa full info.
    """
    # Query tối ưu (Vẫn cần prefetch/select_related)
    course_models = Course.objects.select_related(
        'owner', 'subject'
    ).prefetch_related(
        'categories', 'tags', 'files'
    ).order_by('-created_at')
    
    # Gọi Factory Method mới
    return [CourseDomain.from_model_overview_admin(course_domain) for course_domain in course_models]


def get_course_instructor(owner: UserModel, course_id: uuid) -> CourseDomain:
    """
    Lấy CẤU TRÚC (modules, lessons) của MỘT course.
    Hàm này đồng thời kiểm tra quyền sở hữu (owner).
    """
    try:
        course = Course.objects.prefetch_related(
            'categories', 
            'tags',
            'modules',                  # << Prefetch modules
            'modules__lessons'          # << Prefetch lessons lồng trong modules
            # KHÔNG prefetch 'modules__lessons__content_blocks'
        ).get(owner=owner, id=course_id)
        
        # Hàm from_model này sẽ tạo cây domain
        return CourseDomain.from_model(course)

    except Course.DoesNotExist:
        # Nếu không tìm thấy (do sai ID hoặc sai owner) -> Báo lỗi
        raise DomainError("Không tìm thấy khóa học hoặc bạn không có quyền.")


# --- CÁC HÀM AGGREGATE (PUBLISH/UNPUBLISH) CHO INSTRUCTOR ---



# @transaction.atomic
# def publish_course_for_instructor(course_id: str, publish_data: Any, owner: UserModel) -> CourseDomain:
#     """
#     Publish một course
#     """
#     # Lấy Aggregate Root (đã check quyền sở hữu)
#     course_domain = get_course_for_instructor(course_id, owner)
    
#     # Gọi hàm publish 
#     require_all = getattr(publish_data, 'require_all_lessons_published', False)
#     try:
#         course_domain.publish(require_all_lessons_published=require_all)
#     except InvalidOperation as e:
#         raise e
    
#     # Lưu trạng thái 
#     try:
#         course_model = Course.objects.get(id=course_id, owner=owner) 
#         course_model.published = course_domain.published
#         course_model.published_at = course_domain.published_at
#         course_model.save(update_fields=['published', 'published_at'])
#         return course_domain
#     except Course.DoesNotExist:
#         raise NotFoundError("Không tìm thấy khóa học để lưu.")
#     except Exception as e:
#         raise DomainError(f"Lỗi khi lưu trạng thái publish: {e}")


# @transaction.atomic
# def unpublish_course_for_instructor(course_id: str, owner: UserModel) -> CourseDomain:
#     """
#     Unpublish một course
#     """
#     # Lấy Aggregate Root (đã check quyền sở hữu)
#     course_domain = get_course_for_instructor(course_id, owner)
    
#     # Gọi logic unpublish
#     course_domain.unpublish()
    
#     # Lưu trạng thái
#     try:
#         course_model = Course.objects.get(id=course_id, owner=owner) 
#         course_model.published = course_domain.published
#         course_model.published_at = course_domain.published_at
#         course_model.save(update_fields=['published', 'published_at'])
#         return course_domain
#     except Course.DoesNotExist:
#         raise NotFoundError("Không tìm thấy khóa học để lưu.")
#     except Exception as e:
#         raise DomainError(f"Lỗi khi lưu trạng thái unpublish: {e}")


