import logging
from typing import Dict, Any, List
from uuid import UUID
from django.db import transaction
from django.db.models import Max, F, Case, When, Value, Prefetch

from content.models import Lesson, Module, LessonVersion, Enrollment, ContentBlock
from content.domains.lesson_domain import LessonDomain
from content.services.exceptions import DomainError, ModuleNotFoundError, LessonNotFoundError, NotEnrolledError, NoPublishedContentError, NoVersionFoundError

logger = logging.getLogger(__name__)

def list_lessons_for_module(module_id: UUID) -> List[LessonDomain]:
    """
    Lấy danh sách tất cả các bài học cho một module cụ thể,
    được sắp xếp theo thứ tự.
    """
    # 1. Kiểm tra xem module có tồn tại không
    if not Module.objects.filter(pk=module_id).exists():
        raise ModuleNotFoundError("Module not found.")

    # 2. Lấy các bài học và sắp xếp
    lessons = Lesson.objects.filter(module_id=module_id).order_by('order')

    # 3. Chuyển đổi sang Domain (giống như list_all_users_for_admin)
    lesson_domains = [LessonDomain.from_model(lesson) for lesson in lessons]
    return lesson_domains


@transaction.atomic
def create_lesson(module_id: UUID, data: Dict[str, Any]) -> LessonDomain:
    """
    Tạo một bài học mới (Lesson) cho một Module.
    """
    # 1. Tìm Module cha
    try:
        module = Module.objects.get(pk=module_id)
    except Module.DoesNotExist:
        raise ModuleNotFoundError("Module not found.")

    # 2. Xử lý logic nghiệp vụ (Business Invariants)
    # Kiểm tra tiêu đề trùng lặp TRONG CÙNG module
    if Lesson.objects.filter(module=module, title=data['title']).exists():
        raise DomainError(f"Bài học với tiêu đề '{data['title']}' đã tồn tại trong module này.")

    # 3. Xác định thứ tự (order)
    # Bài học mới luôn được thêm vào cuối cùng
    current_max_order = Lesson.objects.filter(module=module).aggregate(
        max_order=Max('order')
    )['max_order'] or 0
    
    new_order = current_max_order + 1

    # 4. Tạo Domain object (giống như register_user)
    try:
        lesson_domain = LessonDomain(
            title=data['title'],
            module_id=module_id,
            order=new_order,
            lesson_type=data.get('lesson_type', 'text'), # Giá trị mặc định
            content=data.get('content', ''),
            is_public=data.get('is_public', True)
        )
        
        # Thêm các trường khác từ 'data' nếu có
        # (Giả sử LessonDomain của bạn chấp nhận chúng)

    except Exception as e:
        logger.error(f"Lỗi khi khởi tạo LessonDomain: {e}")
        raise DomainError(f"Dữ liệu đầu vào không hợp lệ: {e}")

    # 5. Chuyển đổi sang Model và lưu
    lesson_model = lesson_domain.to_model()
    lesson_model.module = module  # Gán instance Module đã truy vấn
    lesson_model.save()

    # 6. Trả về domain object đã được tạo (với ID)
    return LessonDomain.from_model(lesson_model)


def update_lesson(lesson_id: UUID, updates: Dict[str, Any]) -> LessonDomain:
    """
    Cập nhật một bài học (Lesson) từ dữ liệu được cung cấp.
    """
    # 1. Tìm bài học (giống như update_user)
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
    except Lesson.DoesNotExist:
        raise LessonNotFoundError("Lesson not found.")

    # 2. Xử lý logic nghiệp vụ (Business Invariants)
    # Nếu tiêu đề được cập nhật, kiểm tra trùng lặp
    if 'title' in updates:
        if Lesson.objects.filter(
            module=lesson.module, 
            title=updates['title']
        ).exclude(pk=lesson_id).exists():
            raise DomainError(f"Bài học với tiêu đề '{updates['title']}' đã tồn tại trong module này.")

    # 3. Áp dụng các cập nhật vào model
    # (Giả sử Pydantic DTO (LessonUpdateInput) đã lọc các trường)
    for key, value in updates.items():
        if hasattr(lesson, key):
            setattr(lesson, key, value)
    
    lesson.save()

    # 4. Trả về domain object đã cập nhật
    return LessonDomain.from_model(lesson)


@transaction.atomic
def delete_lesson(lesson_id: UUID):
    """
    Xóa một bài học và cập nhật lại thứ tự của các bài học còn lại.
    """
    # 1. Tìm bài học
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
    except Lesson.DoesNotExist:
        raise LessonNotFoundError("Lesson not found.")

    module_id = lesson.module_id
    deleted_order = lesson.order

    # 2. Xóa bài học (giống như delete_user)
    lesson.delete()

    # 3. Xử lý logic nghiệp vụ: Lấp đầy khoảng trống thứ tự
    # Giảm 'order' của tất cả các bài học sau bài bị xóa đi 1
    Lesson.objects.filter(
        module_id=module_id, 
        order__gt=deleted_order
    ).update(order=F('order') - 1)


@transaction.atomic
def reorder_lessons(module_id: UUID, lesson_ids: List[UUID]):
    """
    Sắp xếp lại thứ tự của tất cả các bài học trong một module
    dựa trên một danh sách ID đã định sẵn.
    """
    # Kiểm tra module
    try:
        module = Module.objects.get(pk=module_id)
    except Module.DoesNotExist:
        raise ModuleNotFoundError("Module not found.")

    # Logic nghiệp vụ: Xác thực danh sách
    # Lấy tất cả ID bài học hiện tại trong module
    current_lesson_ids = set(
        Lesson.objects.filter(module=module).values_list('id', flat=True)
    )
    
    # Lấy các ID từ input
    new_lesson_ids_set = set(lesson_ids)

    # Kiểm tra xem hai set có khớp nhau không
    if current_lesson_ids != new_lesson_ids_set:
        logger.warning(f"Reorder failed: Mismatch. Current: {current_lesson_ids}, New: {new_lesson_ids_set}")
        raise DomainError("Danh sách bài học không đầy đủ hoặc chứa ID không hợp lệ cho module này.")
        
    # Thực hiện cập nhật thứ tự
    # Sử dụng Case/When để cập nhật hàng loạt (hiệu quả hơn N truy vấn)
    when_clauses = [
        When(pk=lesson_id, then=Value(index + 1)) 
        for index, lesson_id in enumerate(lesson_ids)
    ]
    
    if not when_clauses:
        return # Không có gì để cập nhật

    Lesson.objects.filter(
        module_id=module_id
    ).update(order=Case(*when_clauses))


def get_published_lesson_content(user, lesson_id: str):
    """
    Lấy nội dung bài học đã được xuất bản cho một người học.

    Quy tắc nghiệp vụ:
    1. Bài học (Lesson) phải tồn tại và `published=True`.
    2. Người dùng (user) phải ghi danh (enrolled) vào khóa học chứa bài học đó.
    3. Phải có ít nhất một phiên bản (LessonVersion) với status='published'.
    4. Trả về phiên bản 'published' mới nhất.
    """
    
    try:
        # Lấy bài học và kiểm tra xem nó đã publish chưa
        # Tối ưu DB query bằng select_related
        lesson = Lesson.objects.select_related(
            'module__course'
        ).get(pk=lesson_id, published=True)
        
    except Lesson.DoesNotExist:
        # Nếu không tìm thấy (hoặc lesson.published=False)
        raise LessonNotFoundError("Không tìm thấy bài học hoặc bài học chưa được xuất bản.")

    # Kiểm tra quyền ghi danh (Enrollment)
    course = lesson.module.course
    is_enrolled = Enrollment.objects.filter(user=user, course=course).exists()
    
    if not is_enrolled:
        # User đã login nhưng chưa ghi danh
        raise NotEnrolledError("Bạn chưa ghi danh vào khóa học này.")

    # Lấy phiên bản đã 'published' mới nhất
    # Dùng prefetch_related để lấy tất cả content_blocks
    # chỉ bằng 2 câu truy vấn
    published_version = LessonVersion.objects.prefetch_related(
        Prefetch(
            'content_blocks', 
            queryset=ContentBlock.objects.order_by('position')
        )
    ).filter(
        lesson=lesson, 
        status='published'
    ).order_by('-version').first() # Lấy version mới nhất

    # Kiểm tra xem có nội dung không
    if not published_version:
        raise NoPublishedContentError("Bài học này hiện chưa có nội dung được xuất bản.")
        
    # Trả về domain object (model instance)
    return published_version


def get_lesson_preview(lesson_id: str):
    """
    Lấy nội dung xem trước (preview) cho Admin hoặc Instructor.

    Quy tắc nghiệp vụ:
    1. Bài học (Lesson) phải tồn tại (không cần `published=True`).
    2. Trả về phiên bản (LessonVersion) MỚI NHẤT, bất kể status
       (draft, review, hay published).
    """
    
    try:
        # Kiểm tra bài học tồn tại
        lesson = Lesson.objects.get(pk=lesson_id)
        
    except Lesson.DoesNotExist:
        raise LessonNotFoundError("Không tìm thấy bài học.")

    # Lấy phiên bản MỚI NHẤT (latest)
    latest_version = LessonVersion.objects.prefetch_related(
        Prefetch(
            'content_blocks', 
            queryset=ContentBlock.objects.order_by('position')
        )
    ).filter(
        lesson=lesson
    ).order_by('-version').first() # Lấy version mới nhất

    # 3. Kiểm tra xem có bất kỳ version nào không
    if not latest_version:
        raise NoVersionFoundError("Bài học này chưa có bất kỳ phiên bản nội dung nào.")
        
    # 4. Trả về domain object (model instance)
    return latest_version