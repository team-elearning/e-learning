import logging
from typing import Dict, Any, List, Tuple
from uuid import UUID
from django.db import transaction
from django.db.models import Max, F, Case, When, Value, Prefetch

from custom_account.models import UserModel
from content.models import Lesson, Module, ContentBlock
from content.domains.lesson_domain import LessonDomain
from core.exceptions import DomainError, ModuleNotFoundError, LessonNotFoundError, NotEnrolledError, NoPublishedContentError, VersionNotFoundError
from content.services.content_block_service import create_content_block, patch_content_block



logger = logging.getLogger(__name__)

# def list_lessons_for_module(module_id: UUID) -> List[LessonDomain]:
#     """
#     Lấy danh sách tất cả các bài học cho một module cụ thể,
#     được sắp xếp theo thứ tự.
#     """
#     # 1. Kiểm tra xem module có tồn tại không
#     if not Module.objects.filter(pk=module_id).exists():
#         raise ModuleNotFoundError("Module not found.")

#     # 2. Lấy các bài học và sắp xếp
#     lessons = Lesson.objects.filter(module_id=module_id).prefetch_related('content_blocks').order_by('order')

#     # 3. Chuyển đổi sang Domain (giống như list_all_users_for_admin)
#     lesson_domains = [LessonDomain.from_model(lesson) for lesson in lessons]
#     return lesson_domains



def create_lesson(module: Module, data: Dict[str, Any], actor: UserModel) -> Tuple[Lesson, List[str]]:
    """
    Tạo Lesson VÀ các ContentBlock con của nó.
    Kết hợp logic từ file mới của bạn.
    """
    # 1. Tách dữ liệu con
    content_blocks_data = data.get('content_blocks', [])
    files_to_commit = []

    # 2. Xử lý logic Lesson (Lấy từ code mới của bạn)
    title = data.get('title')

    # (Sử dụng 'position' thay vì 'order' cho nhất quán)
    position = data.get('position')
    if position is None:
        current_max_pos = Lesson.objects.filter(module=module).aggregate(
            max_pos=Max('position')
        )['max_pos'] or 0
        position = 0 if current_max_pos is None else current_max_pos + 1

    

    # 3. Tạo Lesson (data giờ chỉ còn của lesson)
    # **data chứa (title, content_type, published...)
    new_lesson = Lesson.objects.create(
        module=module,
        title=title,
        position=position,
    )
    
    # 4. ỦY QUYỀN cho hàm 'create_content_block' (Hàm 4)
    for block_data in content_blocks_data:
        block, block_files = create_content_block(
            lesson=new_lesson,
            data=block_data,
            actor=actor
        )
        files_to_commit.extend(block_files)

    return LessonDomain.from_model(new_lesson), files_to_commit


def patch_lesson(lesson_id: UUID, data: Dict[str, Any]) -> Tuple[LessonDomain, List[str]]:
    """
    Cập nhật (PATCH) một Lesson và xử lý lồng nhau 
    cho ContentBlocks theo logic "Moodle" (Create, Update, Delete).
    """
    
    # 1. Lấy đối tượng gốc
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        raise ValueError(f"Lesson với id {lesson_id} không tìm thấy.")

    # 2. Tách dữ liệu con
    content_blocks_data = data.get('content_blocks', None) # None = "không thay đổi"
    files_to_commit = []

    # 3. Cập nhật các trường đơn giản của Lesson
    simple_fields = ['title', 'position', 'content_type', 'published']
    update_fields_for_save = []

    for field in simple_fields:
        if field in data:
            setattr(lesson, field, data[field])
            update_fields_for_save.append(field)
        
    lesson.save(update_fields=update_fields_for_save)

    # 4. Xử lý ContentBlocks lồng nhau (LOGIC MOODLE)
    if content_blocks_data is not None: # Chỉ chạy nếu key 'content_blocks' tồn tại
        
        # Lấy ID các block hiện tại trong DB
        existing_block_ids = set(
            lesson.content_blocks.values_list('id', flat=True)
        )
        incoming_block_ids = set()

        # 1. Xử lý Cập nhật (Update) và Tạo mới (Create)
        for position, block_data in enumerate(content_blocks_data):
            block_data['position'] = position # Gán lại vị trí mới
            block_id_str = block_data.get('id')
            block_position = block_data.get('position')

            if block_id_str:
                # --- UPDATE (PATCH) ---
                try:
                    block_id = UUID(str(block_id_str))
                except ValueError:
                    raise ValueError(f"Sai format ContentBlock ID: {block_id_str}")

                if block_id not in existing_block_ids:
                    raise ValueError(f"Block {block_id_str} với vị trí {block_position} không thuộc về lesson này.")
                
                # Ủy quyền cho hàm patch_content_block (Hàm 2)
                updated_block_domain, block_files = patch_content_block(
                    block_id=block_id,
                    data=block_data
                )
                files_to_commit.extend(block_files)
                incoming_block_ids.add(block_id)

            else:
                # --- CREATE ---
                # Ủy quyền cho hàm create_content_block bạn đã cung cấp
                new_block_domain, block_files = create_content_block(
                    lesson=lesson,
                    data=block_data
                )
                files_to_commit.extend(block_files)
                incoming_block_ids.add(new_block_domain.id) # Lấy ID từ domain

        # 2. Xử lý Xóa (Delete)
        ids_to_delete = existing_block_ids - incoming_block_ids
        if ids_to_delete:
            ContentBlock.objects.filter(id__in=ids_to_delete).delete()

    # 5. Trả về
    # from_model sẽ tự động query lại content_blocks.all() mới nhất
    return LessonDomain.from_model(lesson), files_to_commit


# @transaction.atomic
# def delete_lesson(lesson_id: UUID):
#     """
#     Xóa một bài học và cập nhật lại thứ tự của các bài học còn lại.
#     """
#     # 1. Tìm bài học
#     try:
#         lesson = Lesson.objects.get(pk=lesson_id)
#     except Lesson.DoesNotExist:
#         raise LessonNotFoundError("Lesson not found.")

#     module_id = lesson.module_id
#     deleted_order = lesson.order

#     # 2. Xóa bài học (giống như delete_user)
#     lesson.delete()

#     # 3. Xử lý logic nghiệp vụ: Lấp đầy khoảng trống thứ tự
#     # Giảm 'order' của tất cả các bài học sau bài bị xóa đi 1
#     Lesson.objects.filter(
#         module_id=module_id, 
#         order__gt=deleted_order
#     ).update(order=F('order') - 1)


# @transaction.atomic
# def reorder_lessons(module_id: UUID, lesson_ids: List[UUID]):
#     """
#     Sắp xếp lại thứ tự của tất cả các bài học trong một module
#     dựa trên một danh sách ID đã định sẵn.
#     """
#     # Kiểm tra module
#     try:
#         module = Module.objects.get(pk=module_id)
#     except Module.DoesNotExist:
#         raise ModuleNotFoundError("Module not found.")

#     # Logic nghiệp vụ: Xác thực danh sách
#     # Lấy tất cả ID bài học hiện tại trong module
#     current_lesson_ids = set(
#         Lesson.objects.filter(module=module).values_list('id', flat=True)
#     )
    
#     # Lấy các ID từ input
#     new_lesson_ids_set = set(lesson_ids)

#     # Kiểm tra xem hai set có khớp nhau không
#     if current_lesson_ids != new_lesson_ids_set:
#         logger.warning(f"Reorder failed: Mismatch. Current: {current_lesson_ids}, New: {new_lesson_ids_set}")
#         raise DomainError("Danh sách bài học không đầy đủ hoặc chứa ID không hợp lệ cho module này.")
        
#     # Thực hiện cập nhật thứ tự
#     # Sử dụng Case/When để cập nhật hàng loạt (hiệu quả hơn N truy vấn)
#     when_clauses = [
#         When(pk=lesson_id, then=Value(index + 1)) 
#         for index, lesson_id in enumerate(lesson_ids)
#     ]
    
#     if not when_clauses:
#         return # Không có gì để cập nhật

#     Lesson.objects.filter(
#         module_id=module_id
#     ).update(order=Case(*when_clauses))


# def get_published_lesson_content(user, lesson_id: str):
#     """
#     Lấy nội dung bài học đã được xuất bản cho một người học.

#     Quy tắc nghiệp vụ:
#     1. Bài học (Lesson) phải tồn tại và `published=True`.
#     2. Người dùng (user) phải ghi danh (enrolled) vào khóa học chứa bài học đó.
#     3. Phải có ít nhất một phiên bản (LessonVersion) với status='published'.
#     4. Trả về phiên bản 'published' mới nhất.
#     """
    
#     try:
#         # Lấy bài học và kiểm tra xem nó đã publish chưa
#         # Tối ưu DB query bằng select_related
#         lesson = Lesson.objects.select_related(
#             'module__course'
#         ).get(pk=lesson_id, published=True)
        
#     except Lesson.DoesNotExist:
#         # Nếu không tìm thấy (hoặc lesson.published=False)
#         raise LessonNotFoundError("Không tìm thấy bài học hoặc bài học chưa được xuất bản.")

#     # Kiểm tra quyền ghi danh (Enrollment)
#     course = lesson.module.course
#     is_enrolled = Enrollment.objects.filter(user=user, course=course).exists()
    
#     if not is_enrolled:
#         # User đã login nhưng chưa ghi danh
#         raise NotEnrolledError("Bạn chưa ghi danh vào khóa học này.")

#     # Lấy phiên bản đã 'published' mới nhất
#     # Dùng prefetch_related để lấy tất cả content_blocks
#     # chỉ bằng 2 câu truy vấn
#     published_version = LessonVersion.objects.prefetch_related(
#         Prefetch(
#             'content_blocks', 
#             queryset=ContentBlock.objects.order_by('position')
#         )
#     ).filter(
#         lesson=lesson, 
#         status='published'
#     ).order_by('-version').first() # Lấy version mới nhất

#     # Kiểm tra xem có nội dung không
#     if not published_version:
#         raise NoPublishedContentError("Bài học này hiện chưa có nội dung được xuất bản.")
        
#     # Trả về domain object (model instance)
#     return published_version


# def get_lesson_preview(lesson_id: str):
#     """
#     Lấy nội dung xem trước (preview) cho Admin hoặc Instructor.

#     Quy tắc nghiệp vụ:
#     1. Bài học (Lesson) phải tồn tại (không cần `published=True`).
#     2. Trả về phiên bản (LessonVersion) MỚI NHẤT, bất kể status
#        (draft, review, hay published).
#     """
    
#     try:
#         # Kiểm tra bài học tồn tại
#         lesson = Lesson.objects.get(pk=lesson_id)
        
#     except Lesson.DoesNotExist:
#         raise LessonNotFoundError("Không tìm thấy bài học.")


#     # 3. Kiểm tra xem có bất kỳ version nào không
#     if not lesson:
#         raise VersionNotFoundError("Bài học này chưa có bất kỳ phiên bản nội dung nào.")
        
#     # 4. Trả về domain object 
#     return latest_version