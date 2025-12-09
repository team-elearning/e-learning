import logging
from pydantic import BaseModel
from typing import Type, Any, Optional
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.db.models.query import QuerySet
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.views import APIView

from content.models import ContentBlock



logger = logging.getLogger(__name__)

class DtoMappingError(APIException):
    status_code = 500
    default_detail = 'DTO mapping failed.'
    default_code = 'dto_mapping_error'
    
class RoleBasedOutputMixin:
    """
    Mixin tự động chọn DTO output dựa trên vai trò user và quan hệ với object.
    
    Priority:
    1. Admin/Staff -> output_dto_admin
    2. Owner (Instructor) -> output_dto_instructor (Kiểm tra instance.owner_id == user.id)
    3. Self (User Profile) -> output_dto_self (Kiểm tra instance.id == user.id)
    4. Public -> output_dto_public
    """

    output_dto_public: Type[BaseModel]
    output_dto_admin: Optional[Type[BaseModel]] = None
    output_dto_instructor: Optional[Type[BaseModel]] = None # NEW: DTO cho chủ sở hữu resource
    output_dto_self: Optional[Type[BaseModel]] = None       # DTO cho chính bản thân user (Profile)

    def _select_dto_class(self, instance: Any, request) -> Type[BaseModel]:
        """Chọn DTO class phù hợp."""
        user = request.user
        is_auth = user.is_authenticated

        # 1. Admin / Staff -> Admin DTO
        if is_auth and user.is_staff and self.output_dto_admin:
            return self.output_dto_admin

        # 2. Instructor / Owner -> Instructor DTO (NEW LOGIC)
        # Logic: Nếu user là người tạo ra instance này (owner_id khớp)
        if self.output_dto_instructor and is_auth:
            # Lấy owner_id từ instance (Domain Object hoặc Model đều thường có field này)
            # Dùng getattr để tránh lỗi nếu object không có field owner
            obj_owner_id = getattr(instance, 'owner_id', getattr(instance, 'owner', None))
            
            # Nếu owner là object User, lấy ID của nó
            if hasattr(obj_owner_id, 'id'):
                obj_owner_id = obj_owner_id.id

            # So sánh ID (chuyển về string hoặc uuid để so sánh an toàn)
            if str(obj_owner_id) == str(user.id):
                return self.output_dto_instructor

        # 3. Self -> Self DTO (Dùng cho User Profile)
        # Logic: instance chính là user đang login
        if (self.output_dto_self 
            and is_auth
            and str(getattr(instance, "id", "")) == str(user.id)):
            return self.output_dto_self

        # 4. Fallback -> Public DTO
        return self.output_dto_public

    def _to_dto(self, instance: Any, request) -> BaseModel:
        """Convert a domain object → selected DTO."""
        dto_cls = self._select_dto_class(instance, request)
        # `from_orm` works with Django models, SQLAlchemy, etc.
        return dto_cls.model_validate(instance) # Pydantic v2

    def finalize_response(self, request, response, *args, **kwargs):
        """
        DRF calls this *after* the view returns a Response.
        We intercept and replace the payload if it contains {"instance": ...}
        """
        if isinstance(response.data, dict) and "instance" in response.data:
            instance_data = response.data["instance"]
            is_list = isinstance(instance_data, (list, QuerySet))

            try:
                if is_list:
                    # --- XỬ LÝ LIST ---
                    # Gọi _to_dto cho TỪNG item
                    # (Điều này cũng sửa một bug: cho phép 
                    #  trả về output_dto_self và output_dto_public
                    #  trong cùng 1 list)
                    response.data = [
                        self._to_dto(item, request).model_dump()
                        for item in instance_data
                    ]
                
                else:
                    # --- XỬ LÝ OBJECT ĐƠN LẺ ---
                    # Gọi _to_dto và chuyển thành dict
                    response.data = self._to_dto(instance_data, request).model_dump()
            
            except Exception as e:
                # (Thêm exc_info=True để debug dễ hơn)
                logger.error(f"DTO mapping/serialization failed: {e}", exc_info=True) 
                raise DtoMappingError(f"DTO mapping/serialization failed: {e}")

        # Gọi hàm finalize_response gốc của APIView
        return APIView.finalize_response(self, request, response, *args, **kwargs)
    

class AutoPermissionCheckMixin:
    """
    Mixin tự động lấy object từ URL và check quyền sở hữu/truy cập 
    trước khi request vào đến hàm xử lý chính (get/post/put...).
    
    Cách dùng:
    1. Kế thừa Mixin này trong APIView.
    2. Khai báo biến `permission_lookup`.
       Ví dụ: permission_lookup = {'module_id': Module, 'course_id': Course}
    """
    permission_lookup = {}  # Format: {'url_kwarg_name': ModelClass}

    def initial(self, request, *args, **kwargs):
        # 1. Chạy logic khởi tạo mặc định của DRF (Authentication, Throttling...)
        super().initial(request, *args, **kwargs)

        # 2. Duyệt qua cấu hình lookup để tìm và check quyền
        for url_param, model_class in self.permission_lookup.items():
            if url_param in kwargs:
                obj_id = kwargs[url_param]
                
                # a. Query DB (Tự động raise 404 nếu không thấy)
                obj = get_object_or_404(model_class, pk=obj_id)
                
                # b. Check Object Permissions (Kích hoạt IsCourseOwner, IsInstructor...)
                # Nếu fail, DRF tự raise 403 Forbidden
                self.check_object_permissions(request, obj)
                
                # c. Gắn object vào view instance để dùng lại (DRY)
                # Ví dụ: Model là 'Module' -> self.module = obj
                model_name = model_class._meta.model_name # 'module', 'course', 'lesson'...
                setattr(self, model_name, obj)


# class ModulePermissionMixin:
#     """
#     Mixin này cung cấp một hàm helper để kiểm tra xem
#     request.user có phải là admin hoặc owner của module
#     được chỉ định trong URL (module_id) hay không.
    
#     Nó được thiết kế để gọi TỪ BÊN TRONG một phương thức view (như post).
#     """
    
#     def check_module_permission(self, request, module_id):
#         """
#         Kiểm tra quyền (Admin hoặc Module Owner) bằng tay.
#         Raises Http404 nếu không tìm thấy Module.
#         Raises PermissionDenied nếu không có quyền.
#         """
#         try:
#             # Dùng select_related để tối ưu
#             module = Module.objects.select_related('course__owner').get(pk=module_id)
#         except Module.DoesNotExist:
#             raise Http404("Module không tìm thấy.")
            
#         is_admin = request.user.is_staff
#         is_owner = (hasattr(module, 'course') and 
#                     hasattr(module.course, 'owner') and 
#                     module.course.owner == request.user)

#         if not (is_admin or is_owner):
#             raise PermissionDenied("Bạn không phải là chủ sở hữu của module này.")
        
#         # Trả về module để view có thể tái sử dụng
#         return module
    

# class CoursePermissionMixin:
#     """
#     Mixin này kiểm tra xem user có phải là admin hoặc 
#     owner của Course được chỉ định (course_id) hay không.
#     """
    
#     def check_course_permission(self, request, course_id):
#         """
#         Kiểm tra quyền (Admin hoặc Course Owner) bằng tay.
#         Raises Http404 nếu không tìm thấy Course.
#         Raises PermissionDenied nếu không có quyền.
#         """
#         try:
#             course = Course.objects.select_related('owner').get(pk=course_id)
#         except Course.DoesNotExist:
#             raise Http404("Course không tìm thấy.")
            
#         is_admin = request.user.is_staff
#         is_owner = (hasattr(course, 'owner') and 
#                     course.owner == request.user)

#         if not (is_admin or is_owner):
#             raise PermissionDenied("Bạn không phải là chủ sở hữu của khóa học này.")
        
#         # Trả về course để view có thể tái sử dụng
#         return course
    

# class LessonPermissionMixin:
#     """
#     Mixin này cung cấp hàm helper để kiểm tra xem request.user
#     có phải là Admin hoặc Owner (Instructor) của Lesson hay không.
    
#     Quyền được xác định bằng cách kiểm tra owner của Course chứa Lesson.
#     """
    
#     def check_lesson_permission(self, request, lesson_id):
#         """
#         Kiểm tra quyền (Admin hoặc Course Owner) cho một Lesson.
#         Raises Http404 nếu không tìm thấy Lesson.
#         Raises PermissionDenied nếu không có quyền.
#         """
#         try:
#             # Tối ưu query bằng cách join thẳng đến course owner
#             lesson = Lesson.objects.select_related(
#                 'module__course__owner'
#             ).get(pk=lesson_id)
            
#         except Lesson.DoesNotExist:
#             raise Http404("Bài học không tìm thấy.")
            
#         is_admin = request.user.is_staff
        
#         # Kiểm tra chain: lesson -> module -> course -> owner
#         is_owner = (
#             hasattr(lesson, 'module') and
#             hasattr(lesson.module, 'course') and
#             hasattr(lesson.module.course, 'owner') and
#             lesson.module.course.owner == request.user
#         )

#         if not (is_admin or is_owner):
#             raise PermissionDenied("Bạn không có quyền truy cập tài nguyên bài học này.")
            
#         # Trả về lesson để view có thể tái sử dụng nếu cần
#         return lesson
    

# class LessonVersionPermissionMixin:
#     """
#     Kiểm tra quyền (Admin hoặc Owner) cho một LessonVersion.
#     Quyền được suy ra từ Lesson -> Module -> Course -> Owner.
#     """
#     def check_lesson_version_permission(self, request, lesson_version_id):
#         if not request.user.is_authenticated:
#             raise AuthenticationFailed()
            
#         try:
#             # Join sâu để lấy owner chỉ bằng 1 query
#             version = LessonVersion.objects.select_related(
#                 'lesson__module__course__owner'
#             ).get(pk=lesson_version_id)
#         except LessonVersion.DoesNotExist:
#             raise Http404("Lesson Version không tìm thấy.")

#         is_admin = request.user.is_staff
        
#         # Chain: version -> lesson -> module -> course -> owner
#         try:
#             # Dùng .id để tránh lỗi so sánh object (nếu request.user là SimpleLazyObject)
#             is_owner = (
#                 version.lesson.module.course.owner.id == request.user.id
#             )
#         except AttributeError:
#             # Handle chain breaks (e.g., lesson.module is None)
#             is_owner = False

#         if not (is_admin or is_owner):
#             raise PermissionDenied("Bạn không có quyền truy cập lesson version này.")
        
#         return version # Trả về để tái sử dụng

class ContentBlockPermissionMixin:
    """
    Kiểm tra quyền (Admin hoặc Owner) cho một ContentBlock.
    Quyền được suy ra từ Block -> Version -> Lesson -> ...
    """
    def check_content_block_permission(self, request, pk):
        if not request.user.is_authenticated:
            raise AuthenticationFailed()
            
        try:
            block = ContentBlock.objects.select_related(
                'lesson_version__lesson__module__course__owner'
            ).get(pk=pk)
        except ContentBlock.DoesNotExist:
            raise Http404("Content Block không tìm thấy.")

        is_admin = request.user.is_staff
        
        # Chain: block -> version -> lesson -> module -> course -> owner
        try:
            is_owner = (
                block.lesson_version.lesson.module.course.owner.id == request.user.id
            )
        except AttributeError:
            is_owner = False

        if not (is_admin or is_owner):
            raise PermissionDenied("Bạn không có quyền truy cập content block này.")
        
        return block # Trả về để tái sử dụng
    