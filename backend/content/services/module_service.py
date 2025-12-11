import uuid
from typing import Any, Dict, List, Tuple
from django.db import transaction
from django.db.models import Max, F

from core.exceptions import DomainError
from custom_account.models import UserModel
from content.services.lesson_service import create_lesson_from_template
from content.domains.module_domain import ModuleDomain
from content.models import Module, Course, Lesson



# ==========================================
# GET
# ==========================================

def get_modules(course_id: uuid.UUID) -> list[ModuleDomain]:
    """Lấy danh sách modules của course"""
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        raise Course.DoesNotExist(f"Course với ID '{course_id}' không tồn tại.")
    
    modules = Module.objects.filter(course=course).order_by('position')
    return [ModuleDomain.from_model(module) for module in modules]


def get_module_detail(module_id: uuid.UUID) -> ModuleDomain:
    """Lấy chi tiết module"""
    try:
        module = Module.objects.select_related('course').prefetch_related('lessons').get(id=module_id)
    except Module.DoesNotExist:
        raise Module.DoesNotExist(f"Module với ID '{module_id}' không tồn tại.")
    
    return ModuleDomain.from_model(module)


# ==========================================
# CREATE
# ==========================================

@transaction.atomic
def create_module(
    course_id: uuid.UUID, 
    data: dict
) -> ModuleDomain:
    """Tạo module mới"""
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        raise Course.DoesNotExist(f"Course với ID '{course_id}' không tồn tại.")
    
    max_position = Module.objects.filter(course=course).aggregate(
        Max('position')
    )['position__max']
    
    # 2. Tính vị trí mới (nếu chưa có module nào thì là 0, có rồi thì +1)
    new_position = 0 if max_position is None else max_position + 1

    # Tạo module
    module = Module.objects.create(
        course=course,
        title=data.get('title') or "Untitled",
        position=new_position
    )
    
    return ModuleDomain.from_model(module)


# ==========================================
# PUBLIC INTERFACE (UPDATE)
# ==========================================

@transaction.atomic
def update_module(
    module_id: uuid.UUID, 
    data: dict, 
) -> ModuleDomain:
    """Update module"""
    try:
        module = Module.objects.select_related('course').get(id=module_id)
    except Module.DoesNotExist:
        raise Module.DoesNotExist(f"Module với ID '{module_id}' không tồn tại.")
    
    # Update fields
    if 'title' in data:
        module.title = data['title']
    module.save()

    return ModuleDomain.from_model_metadata(module)


# ==========================================
# PUBLIC INTERFACE (DELETE)
# ==========================================

@transaction.atomic
def delete_module(module_id: uuid.UUID) -> None:
    """Xóa module"""
    try:
        module = Module.objects.select_related('course').get(id=module_id)
    except Module.DoesNotExist:
        raise Module.DoesNotExist(f"Module với ID '{module_id}' không tồn tại.")
        
    module.delete()


# ==========================================
# PUBLIC INTERFACE (REORDER)
# ==========================================

@transaction.atomic
def reorder_modules(course_id: uuid.UUID, module_id_list: list[uuid.UUID]):
    """
    Input: module_id_list = ['uuid-1', 'uuid-3', 'uuid-2']
    """
    # 2. Lấy các module thuộc course đó ra (Dùng in_bulk cho gọn)
    # Filter theo course_id để đảm bảo module thuộc đúng course này (security check)
    modules_dict = Module.objects.filter(course_id=course_id).in_bulk(field_name='id')
    existing_ids_set = set(modules_dict.keys())

    # 2. Parse và Validate input từ Frontend
    input_uuids = []
    try:
        for mid in module_id_list:
            # Nếu mid đã là UUID object thì giữ nguyên, nếu là str thì convert
            val = mid if isinstance(mid, uuid.UUID) else uuid.UUID(str(mid))
            input_uuids.append(val)
    except ValueError:
        raise DomainError("Danh sách ID chứa định dạng không hợp lệ.")

    input_ids_set = set(input_uuids)

    # Kiểm tra độ dài (để bắt lỗi trùng lặp)
    if len(input_uuids) != len(existing_ids_set):
        raise DomainError(
            f"Dữ liệu không đồng bộ. DB có {len(existing_ids_set)} modules, "
            f"nhưng nhận được {len(input_uuids)}. Vui lòng reload trang."
        )
    
    # Kiểm tra 2: Các phần tử có khớp hoàn toàn không?
    # Nếu input chứa ID của course khác -> Set sẽ lệch nhau ngay
    if input_ids_set != existing_ids_set:
        raise DomainError("Danh sách ID gửi lên không khớp với dữ liệu hệ thống (có thể chứa ID lạ hoặc thiếu sót).")

    update_list = []
    ordered_modules = []

    # 3. Loop và gán position dựa trên index
    for index, mod_id in enumerate(module_id_list):
        module = modules_dict[mod_id] # Chắc chắn tồn tại nhờ check bên trên
        
        ordered_modules.append(module)
        
        if module.position != index:
            module.position = index
            update_list.append(module)

    # 4. Bulk update
    if update_list:
        Module.objects.bulk_update(update_list, ['position'])

    return [ModuleDomain.from_model(m) for m in ordered_modules]    
    

# ==========================================
# TEMPLATE
# ==========================================

def create_module_from_template(course: Course, data: Dict[str, Any], actor: UserModel) -> Tuple[ModuleDomain, List[str]]:
    """
    Tạo một module VÀ CÁC CON (lesson, content_block) của nó.
    Hàm này được gọi BÊN TRONG một transaction (của create_course).
    """
    # 1. Tách dữ liệu con (lessons) ra khỏi dữ liệu (module)
    lessons_data = data.get('lessons', [])

    # 2. Xử lý logic nghiệp vụ của Module (lấy từ code cũ của bạn)
    title = data.get('title')

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
        create_lesson_from_template(
            module=new_module, 
            data=lesson_data,
            actor=actor
        )
    
    # 5. Trả về module đã tạo VÀ danh sách file đã gom
    return ModuleDomain.from_model(new_module)



# def patch_module(module_id: uuid.UUID, data: dict) -> Tuple[Module, List[uuid.UUID]]:
#     """
#     Hàm này tự nó cũng phải làm logic PATCH lồng nhau cho Lessons.
#     """
    
#     # 1. Lấy module
#     try:
#         module = Module.objects.get(id=module_id)
#     except Module.DoesNotExist:
#         raise ValueError("Module not found.")

#     # 2. Tách data
#     lessons_data = data.get('lessons', None)
#     files_to_commit = [] # Tương lai có thể dùng cho file của module

#     # 3. Cập nhật trường đơn giản của Module
#     simple_fields = ['title', 'position', 'description'] # v.v.
#     for field in simple_fields:
#         if field in data:
#             setattr(module, field, data[field])
    
#     module.save() # Lưu thay đổi của Module

#     # 4. Xử lý Lessons (Logic "Moodle" y hệt như course/module)
#     if lessons_data is not None:
#         existing_lesson_ids = set(module.lessons.values_list('id', flat=True))
#         incoming_lesson_ids = set()
        
#         for position, lesson_data in enumerate(lessons_data):
#             lesson_data['position'] = position
#             lesson_id_str = lesson_data.get('id')
            
#             if lesson_id_str:
#                 # --- UPDATE LESSON ---
#                 lesson_id = uuid.UUID(str(lesson_id_str))
#                 if lesson_id not in existing_lesson_ids:
#                     raise ValueError(f"Lesson {lesson_id} không thuộc về module này.")
                
#                 # Ủy quyền cho lesson_service.patch_lesson
#                 updated_lesson, lesson_files = patch_lesson(
#                     lesson_id=lesson_id, 
#                     data=lesson_data
#                 )
#                 files_to_commit.extend(lesson_files)
#                 incoming_lesson_ids.add(lesson_id)
#             else:
#                 # --- CREATE LESSON ---
#                 new_lesson, lesson_files = create_lesson(
#                     module=module, 
#                     data=lesson_data
#                 )
#                 files_to_commit.extend(lesson_files)
#                 incoming_lesson_ids.add(new_lesson.id)

#         # --- DELETE LESSONS ---
#         ids_to_delete = existing_lesson_ids - incoming_lesson_ids
#         if ids_to_delete:
#             Lesson.objects.filter(id__in=ids_to_delete).delete()

#     return ModuleDomain.from_model(module), files_to_commit


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
