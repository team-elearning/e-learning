import uuid
from typing import Any, Dict, List
from django.db import transaction
from django.db.models import Prefetch
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from content.models import Course
from custom_account.models import UserModel 
from content.domains.course_domain import CourseDomain
from content.services.exceptions import DomainError, CourseNotFoundError, NotFoundError, InvalidOperation
from content.models import Course, Module, Lesson, LessonVersion, Enrollment



@transaction.atomic
def create_course(data: dict, owner: UserModel) -> CourseDomain:
    """
    Tạo một course mới và các quan hệ của nó.
    'data' là dict đã được validate từ Serializer/Input DTO.
    'owner' là user instance (ví dụ: request.user).
    """

    # 1. Kiểm tra các quy tắc nghiệp vụ (ví dụ: title là duy nhất)
    # (Bạn có thể bỏ qua nếu không cần)
    if Course.objects.filter(title=data['title']).exists():
        raise DomainError(f"Một khóa học với tiêu đề '{data['title']}' đã tồn tại.")

    # 2. Tách các trường M2M và FK ra khỏi 'data'
    category_ids = data.pop('categories', [])
    tag_ids = data.pop('tags', [])
    subject_id = data.pop('subject', None) # Giả sử DTO gửi 'subject' là subject_id

    # 3. Tạo Domain object (giống pattern của register_user)
    # Chúng ta thêm owner và subject_id vào data để Pydantic validate
    domain_data = {**data, "owner_id": owner.id, "subject_id": subject_id}
    
    try:
        course_domain = CourseDomain(**domain_data)
    except Exception as e: # Bắt lỗi validation của Pydantic
        raise DomainError(f"Dữ liệu tạo course không hợp lệ: {e}")

    # 4. Chuyển domain sang model
    course = course_domain.to_model()

    # 5. Lưu model chính (để lấy ID)
    course.save()

    # 6. Set các quan hệ M2M
    if category_ids:
        course.categories.set(category_ids)
    if tag_ids:
        course.tags.set(tag_ids)

    # 7. Trả về Domain object từ model đã lưu (giống pattern của register_user)
    return CourseDomain.from_model(course)


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


def delete_course(course_id: uuid.UUID):
    """
    Xóa một course.
    (Giống pattern của delete_user)
    """
    try:
        course_to_delete = Course.objects.get(id=course_id)
    except ObjectDoesNotExist:
        raise CourseNotFoundError("Không tìm thấy khóa học để xóa.")
    
    # Business logic (nếu có):
    # Ví dụ: if course_to_delete.has_active_students:
    #           raise DomainError("Không thể xóa course đang có học viên.")
    
    course_to_delete.delete()
    
    # (Hàm delete_user của bạn không trả về gì, 
    #  nhưng sẽ tốt hơn nếu trả về True)
    # return True


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
                        queryset=Lesson.objects.all().order_by('position').prefetch_related(
                            Prefetch(
                                'versions', # Giả định related_name='versions' (đúng)
                                queryset=LessonVersion.objects.all().order_by('-version')
                            )
                        )
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


def get_course_by_id_for_instructor(course_id: uuid.UUID, owner: UserModel) -> CourseDomain:
    """
    Lấy một course theo ID, NHƯNG phải check quyền sở hữu.
    """
    try:
        # Lấy course VÀ lọc theo owner
        course = Course.objects.select_related(
            'owner', 'subject'
        ).prefetch_related(
            'categories', 'tags'
        ).get(pk=course_id, owner=owner) 
        
        return CourseDomain.from_model(course)
        
    except ObjectDoesNotExist:
        raise CourseNotFoundError("Không tìm thấy khóa học.")
    except Exception as e:
        raise DomainError(f"Lỗi khi lấy khóa học: {e}")


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


def delete_course_for_instructor(course_id: uuid.UUID, owner: UserModel):
    """
    Xóa một course, NHƯNG phải check quyền sở hữu.
    """
    try:
        course_to_delete = Course.objects.get(id=course_id, owner=owner) 
    except ObjectDoesNotExist:
        raise CourseNotFoundError("Không tìm thấy khóa học để xóa.")
    
    course_to_delete.delete()
    return True


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
                    Prefetch('lessons', queryset=Lesson.objects.all().order_by('position').prefetch_related(
                        Prefetch('versions', queryset=LessonVersion.objects.all().order_by('-version'))
                    ))
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


