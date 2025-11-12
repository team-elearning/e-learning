from typing import Type, Any
from pydantic import BaseModel
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from django.http import Http404
from django.core.exceptions import PermissionDenied

from content.models import Module, Course, Lesson



class RoleBasedOutputMixin:
    """
    Choose the correct *output* DTO based on the requesting user.

    Expected on the view:
        - `output_dto_public`   → DTO class for normal users
        - `output_dto_admin`    → DTO class for staff / superuser
        - `output_dto_self`     → (optional) DTO for the owner of the object
    """

    output_dto_public: Type[BaseModel]
    output_dto_admin:  Type[BaseModel] | None = None
    output_dto_self:   Type[BaseModel] | None = None

    def _select_dto_class(self, instance: Any, request) -> Type[BaseModel]:
        """Return the DTO class that should be used for the current request."""
        user = request.user

        # 1. Admin / staff → full admin DTO
        if user.is_authenticated and user.is_staff and self.output_dto_admin:
            return self.output_dto_admin

        # 2. Owner of the object → self-DTO (if defined)
        if (hasattr(self, "output_dto_self")
                and self.output_dto_self
                and getattr(instance, "id", None) == getattr(user, "id", None)):
            return self.output_dto_self

        # 3. Fallback → public DTO
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
            domain_obj = response.data["instance"]
            dto_cls = self._select_dto_class(domain_obj, request)
            try:
                # Convert domain_obj to dict
                if hasattr(domain_obj, "model_dump"):  # It's already a Pydantic model
                    data = domain_obj.model_dump()
                elif hasattr(domain_obj, "__dict__"):  # Plain object / dataclass
                    data = domain_obj.__dict__
                else:
                    raise ValueError("Cannot convert domain object to dict")
            
                # Validate + create DTO
                dto_instance = dto_cls.model_validate(data)

                # Serialize to JSON
                response.data = dto_instance.model_dump()
            except Exception as e:
                raise APIException(f"DTO mapping failed: {e}")

        return APIView.finalize_response(self, request, response, *args, **kwargs)
    

class ModulePermissionMixin:
    """
    Mixin này cung cấp một hàm helper để kiểm tra xem
    request.user có phải là admin hoặc owner của module
    được chỉ định trong URL (module_id) hay không.
    
    Nó được thiết kế để gọi TỪ BÊN TRONG một phương thức view (như post).
    """
    
    def check_module_permission(self, request, module_id):
        """
        Kiểm tra quyền (Admin hoặc Module Owner) bằng tay.
        Raises Http404 nếu không tìm thấy Module.
        Raises PermissionDenied nếu không có quyền.
        """
        try:
            # Dùng select_related để tối ưu
            module = Module.objects.select_related('course__owner').get(pk=module_id)
        except Module.DoesNotExist:
            raise Http404("Module không tìm thấy.")
            
        is_admin = request.user.is_staff
        is_owner = (hasattr(module, 'course') and 
                    hasattr(module.course, 'owner') and 
                    module.course.owner == request.user)

        if not (is_admin or is_owner):
            raise PermissionDenied("Bạn không phải là chủ sở hữu của module này.")
        
        # Trả về module để view có thể tái sử dụng
        return module
    

class CoursePermissionMixin:
    """
    Mixin này kiểm tra xem user có phải là admin hoặc 
    owner của Course được chỉ định (course_id) hay không.
    """
    
    def check_course_permission(self, request, course_id):
        """
        Kiểm tra quyền (Admin hoặc Course Owner) bằng tay.
        Raises Http404 nếu không tìm thấy Course.
        Raises PermissionDenied nếu không có quyền.
        """
        try:
            course = Course.objects.select_related('owner').get(pk=course_id)
        except Course.DoesNotExist:
            raise Http404("Course không tìm thấy.")
            
        is_admin = request.user.is_staff
        is_owner = (hasattr(course, 'owner') and 
                    course.owner == request.user)

        if not (is_admin or is_owner):
            raise PermissionDenied("Bạn không phải là chủ sở hữu của khóa học này.")
        
        # Trả về course để view có thể tái sử dụng
        return course
    

class LessonPermissionMixin:
    """
    Mixin này cung cấp hàm helper để kiểm tra xem request.user
    có phải là Admin hoặc Owner (Instructor) của Lesson hay không.
    
    Quyền được xác định bằng cách kiểm tra owner của Course chứa Lesson.
    """
    
    def check_lesson_permission(self, request, lesson_id):
        """
        Kiểm tra quyền (Admin hoặc Course Owner) cho một Lesson.
        Raises Http404 nếu không tìm thấy Lesson.
        Raises PermissionDenied nếu không có quyền.
        """
        try:
            # Tối ưu query bằng cách join thẳng đến course owner
            lesson = Lesson.objects.select_related(
                'module__course__owner'
            ).get(pk=lesson_id)
            
        except Lesson.DoesNotExist:
            raise Http404("Bài học không tìm thấy.")
            
        is_admin = request.user.is_staff
        
        # Kiểm tra chain: lesson -> module -> course -> owner
        is_owner = (
            hasattr(lesson, 'module') and
            hasattr(lesson.module, 'course') and
            hasattr(lesson.module.course, 'owner') and
            lesson.module.course.owner == request.user
        )

        if not (is_admin or is_owner):
            raise PermissionDenied("Bạn không có quyền truy cập tài nguyên bài học này.")
            
        # Trả về lesson để view có thể tái sử dụng nếu cần
        return lesson
