import uuid
from typing import Any, Dict, List, Tuple
from django.db import transaction
from django.db.models import Max, F
from django.core.exceptions import ObjectDoesNotExist

from custom_account.models import UserModel
from content.services.lesson_service import create_lesson, patch_lesson
from content.domains.module_domain import ModuleDomain
from content.models import Module, Course, Lesson




def create_module(course: Course, data: Dict[str, Any], actor: UserModel) -> Tuple[ModuleDomain, List[str]]:
    """
    Tạo một module VÀ CÁC CON (lesson, content_block) của nó.
    Hàm này được gọi BÊN TRONG một transaction (của create_course).
    """
    # 1. Tách dữ liệu con (lessons) ra khỏi dữ liệu (module)
    lessons_data = data.get('lessons', [])
    files_to_commit = [] # Danh sách file của riêng module này

    # 2. Xử lý logic nghiệp vụ của Module (lấy từ code cũ của bạn)
    title = data.get('title')

    position = data.get('position')
    if position is None:
        max_pos_data = Module.objects.filter(course=course).aggregate(max_pos=Max('position'))
        max_pos = max_pos_data.get('max_pos')
        position = 0 if max_pos is None else max_pos + 1
    
    # 3. Tạo Module
    # 'data' lúc này chỉ còn 'title' (và các trường khác nếu có)
    # 'position' đã được tính toán
    new_module = Module.objects.create(
        course=course,
        title=title,
        position=position
        # Hoặc: **data, nếu data từ serializer đã có position
    )
    
    # 4. (QUAN TRỌNG) Gọi hàm con để tạo Lessons
    for lesson_data in lessons_data:
        # Chúng ta cần một hàm tương tự: _create_lesson
        lesson, lesson_files = create_lesson(
            module=new_module, 
            data=lesson_data,
            actor=actor
        )
        files_to_commit.extend(lesson_files) # Gom file từ các lesson con
    
    # 5. Trả về module đã tạo VÀ danh sách file đã gom
    return ModuleDomain.from_model(new_module), files_to_commit


def patch_module(module_id: uuid.UUID, data: dict) -> Tuple[Module, List[uuid.UUID]]:
    """
    Hàm này tự nó cũng phải làm logic PATCH lồng nhau cho Lessons.
    """
    
    # 1. Lấy module
    try:
        module = Module.objects.get(id=module_id)
    except Module.DoesNotExist:
        raise ValueError("Module not found.")

    # 2. Tách data
    lessons_data = data.get('lessons', None)
    files_to_commit = [] # Tương lai có thể dùng cho file của module

    # 3. Cập nhật trường đơn giản của Module
    simple_fields = ['title', 'position', 'description'] # v.v.
    for field in simple_fields:
        if field in data:
            setattr(module, field, data[field])
    
    module.save() # Lưu thay đổi của Module

    # 4. Xử lý Lessons (Logic "Moodle" y hệt như course/module)
    if lessons_data is not None:
        existing_lesson_ids = set(module.lessons.values_list('id', flat=True))
        incoming_lesson_ids = set()
        
        for position, lesson_data in enumerate(lessons_data):
            lesson_data['position'] = position
            lesson_id_str = lesson_data.get('id')
            
            if lesson_id_str:
                # --- UPDATE LESSON ---
                lesson_id = uuid.UUID(str(lesson_id_str))
                if lesson_id not in existing_lesson_ids:
                    raise ValueError(f"Lesson {lesson_id} không thuộc về module này.")
                
                # Ủy quyền cho lesson_service.patch_lesson
                updated_lesson, lesson_files = patch_lesson(
                    lesson_id=lesson_id, 
                    data=lesson_data
                )
                files_to_commit.extend(lesson_files)
                incoming_lesson_ids.add(lesson_id)
            else:
                # --- CREATE LESSON ---
                new_lesson, lesson_files = create_lesson(
                    module=module, 
                    data=lesson_data
                )
                files_to_commit.extend(lesson_files)
                incoming_lesson_ids.add(new_lesson.id)

        # --- DELETE LESSONS ---
        ids_to_delete = existing_lesson_ids - incoming_lesson_ids
        if ids_to_delete:
            Lesson.objects.filter(id__in=ids_to_delete).delete()

    return ModuleDomain.from_model(module), files_to_commit


# def list_modules_for_course(course_id: uuid.UUID) -> List[ModuleDomain]:
#     """
#     Lấy danh sách module (đã sắp xếp) cho một khóa học.
#     """
#     try:
#         Course.objects.get(id=course_id) # Chỉ kiểm tra course tồn tại
#     except ObjectDoesNotExist:
#         raise CourseNotFoundError("Khóa học không tồn tại.")
        
#     module_models = Module.objects.filter(course_id=course_id).order_by('position')
    
#     module_domains = [ModuleDomain.from_model(mod) for mod in module_models]
#     return module_domains


# def get_module_by_id(module_id: uuid.UUID) -> ModuleDomain:
#     """
#     Lấy chi tiết một module bằng ID.
#     (Tương tự get_user_by_id)
#     """
#     try:
#         module = Module.objects.get(id=module_id)
#         return ModuleDomain.from_model(module)
#     except ObjectDoesNotExist:
#         raise ModuleNotFoundError("Module không tìm thấy.")


# @transaction.atomic
# def delete_module(module_id: uuid.UUID):
#     """
#     Xóa một module.
    
#     Logic nghiệp vụ:
#     1. Sau khi xóa, cập nhật lại (giảm 1) 'position' của tất cả các module
#        đứng sau nó trong cùng một khóa học.
#     """
#     try:
#         module_to_delete = Module.objects.get(id=module_id)
#     except ObjectDoesNotExist:
#         raise ModuleNotFoundError("Module không tìm thấy.")
        
#     course = module_to_delete.course
#     deleted_position = module_to_delete.position

#     # Xóa module
#     module_to_delete.delete()
    
#     # Cập nhật position của các module còn lại
#     # (Sử dụng F() để update dựa trên giá trị cũ trong DB)
#     Module.objects.filter(
#         course=course,
#         position__gt=deleted_position
#     ).update(position=F('position') - 1)


# @transaction.atomic
# def reorder_modules(course_id: uuid.UUID, module_ids: List[uuid.UUID]):
#     """
#     Sắp xếp lại thứ tự của tất cả các module trong một khóa học.
    
#     Logic nghiệp vụ:
#     1. Kiểm tra course tồn tại.
#     2. Danh sách `module_ids` phải chứa ĐẦY ĐỦ và ĐÚNG tất cả các ID 
#        của module thuộc khóa học.
#     3. Cập nhật `position` của từng module theo thứ tự trong danh sách.
#     """
#     try:
#         course = Course.objects.get(id=course_id)
#     except ObjectDoesNotExist:
#         raise CourseNotFoundError("Khóa học không tồn tại.")

#     # 2. Validate danh sách ID
#     db_ids = set(
#         Module.objects.filter(course=course).values_list('id', flat=True)
#     )
#     input_ids = set(module_ids)

#     if db_ids != input_ids:
#         raise DomainError(
#             "Danh sách module_ids không khớp với các module hiện tại của khóa học. "
#             "Cần cung cấp đầy đủ ID của tất cả module."
#         )

#     # 3. Cập nhật (sử dụng bulk_update để tối ưu)
#     modules_to_update = []
#     # Lấy map {id: module_object} để giảm truy vấn DB
#     module_map = {m.id: m for m in Module.objects.filter(course=course)}

#     for new_position, module_id in enumerate(module_ids):
#         module_instance = module_map.get(module_id)
        
#         # Chỉ update nếu position thật sự thay đổi
#         if module_instance and module_instance.position != new_position:
#             module_instance.position = new_position
#             modules_to_update.append(module_instance)

#     if modules_to_update:
#         Module.objects.bulk_update(modules_to_update, ['position'])

#     return {
#         "detail": "Thứ tự module đã được cập nhật.",
#         "updated_count": len(modules_to_update)
#     }
