import uuid
from pydantic import ValidationError
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.http import Http404

from content.serializers import ModuleSerializer
from core.api.mixins import RoleBasedOutputMixin, ModulePermissionMixin, CoursePermissionMixin
from content.services import module_service
from content.domains.module_domain import ModuleDomain
from core.exceptions import DomainError
from content.serializers import ModuleSerializer
from core.api.permissions import IsInstructor
from content.api.dtos.module_dto import ModuleInput, ModulePublicOutput, ModuleAdminOutput, ModuleUpdateInput
from content.serializers import ModuleCreateSerializer, ModuleReorderSerializer
from content.models import Course, Module



# Helper để kiểm tra sự tồn tại của Course
def get_course_or_404(course_id: uuid.UUID):
    try:
        return Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        raise Http404("Course not found.")
    
class PublicModuleListView(RoleBasedOutputMixin, APIView):
    """
    GET /courses/<uuid:course_id>/modules/ (Public)
    
    Lấy danh sách các module cho một khóa học.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    output_dto_public = ModulePublicOutput 
    output_dto_admin  = ModuleAdminOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_service = module_service 

    def get(self, request, course_id: uuid.UUID):
        """
        Lấy danh sách tất cả module cho một khóa học.
        """
        try:
            module_domains: list[ModuleDomain] = self.module_service.list_modules_for_course(
                course_id=course_id
            )
            # RoleBasedOutputMixin sẽ tự động chọn DTO phù hợp
            return Response({"instance": module_domains}, status=status.HTTP_200_OK)
        except DomainError as e: # Ví dụ: Course không tìm thấy
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # logger.error(...)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PublicModuleDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /modules/<uuid:pk>/ (Public)
    
    Lấy chi tiết một module.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    output_dto_public = ModulePublicOutput
    output_dto_admin  = ModuleAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_service = module_service

    def get_object(self, pk: uuid.UUID):
        """Hàm helper để kiểm tra module tồn tại."""
        try:
            # Chỉ cần lấy module_id, không cần join phức tạp
            return self.module_service.get_module_by_id(module_id=pk)
        except DomainError: # Service ném "Module không tìm thấy"
            raise Http404("Module not found.")

    def get(self, request, pk: uuid.UUID):
        """
        Lấy chi tiết một module.
        """
        try:
            module_domain: ModuleDomain = self.get_object(pk)
            # RoleBasedOutputMixin sẽ tự động chọn DTO
            return Response({"instance": module_domain}, status=status.HTTP_200_OK)
        except Http404 as e:
             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # logger.error(...)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ------------------ INSTRUCTOR ---------------------------
class InstructorModuleListCreateView(RoleBasedOutputMixin, CoursePermissionMixin, APIView):
    """
    GET /instructor/courses/<uuid:course_id>/modules/
    POST /instructor/courses/<uuid:course_id>/modules/
    
    Yêu cầu IsInstructor và là chủ sở hữu khóa học.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor] 
    
    output_dto_public = ModulePublicOutput 
    output_dto_admin  = ModuleAdminOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_service = module_service 

    def get(self, request, course_id: uuid.UUID):
        """
        Lấy danh sách module (view của Instructor).
        """
        try:
            self.check_course_permission(request, course_id)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        try:
            module_domains: list[ModuleDomain] = self.module_service.list_modules_for_course(
                course_id=course_id
            )
            return Response({"instance": module_domains}, status=status.HTTP_200_OK)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, course_id: uuid.UUID, *args, **kwargs):
        """
        Tạo một module mới cho khóa học (view của Instructor).
        """
        try:
            self.check_course_permission(request, course_id)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        serializer = ModuleSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            module_create_dto = ModuleInput(**validated_data)
        except ValidationError as e: 
            return Response({"detail": f"Dữ liệu đầu vào không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_module_domain: ModuleDomain = self.module_service.create_module(
                course_id=course_id, 
                data=module_create_dto.to_dict()
            )
            return Response(
                {"instance": new_module_domain}, 
                status=status.HTTP_201_CREATED
            )
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # logger.error(...)
            return Response({"detail": "Lỗi không xác định xảy ra trong quá trình tạo module."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstructorModuleDetailView(RoleBasedOutputMixin, ModulePermissionMixin, APIView):
    """
    GET /instructor/modules/<uuid:pk>/
    PUT /instructor/modules/<uuid:pk>/
    PATCH /instructor/modules/<uuid:pk>/
    DELETE /instructor/modules/<uuid:pk>/
    
    Yêu cầu IsInstructor và là chủ sở hữu module.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor] 
    
    output_dto_public = ModulePublicOutput
    output_dto_admin  = ModuleAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_service = module_service
        
    def get(self, request, pk: uuid.UUID):
        """
        Lấy chi tiết một module (view của Instructor).
        """
        try:
            module_instance = self.check_module_permission(request, pk)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        try:
            module_domain: ModuleDomain = self.module_service.get_module_by_id(module_id=pk)
            return Response({"instance": module_domain}, status=status.HTTP_200_OK)
        except DomainError as e: # Service ném lỗi (mặc dù get_object đã check)
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # logger.error(...)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, pk: uuid.UUID):
        """
        Cập nhật một phần (partial update) module.
        """
        try:
            module_instance = self.check_module_permission(request, pk)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        serializer = ModuleSerializer(module_instance, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             
        validated_data = serializer.validated_data

        try:
            update_dto = ModuleUpdateInput(**validated_data)
        except ValidationError as e:
            return Response({"detail": f"Dữ liệu đầu vào không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        updates_payload = update_dto.model_dump(exclude_unset=True) # Dùng exclude_unset cho PATCH

        if not updates_payload:
            module_domain = self.module_service.get_module_by_id(module_id=pk)
            return Response({"instance": module_domain}, status=200)

        try:
            updated_domain: ModuleDomain = self.module_service.update_module(
                module_id=pk, 
                updates=updates_payload
            )
            return Response({"instance": updated_domain}, status=200)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=400)
        except Exception as e:
            # logger.error(...)
            return Response({"detail": "Lỗi không xác định xảy ra trong quá trình cập nhật."}, status=500)

    def delete(self, request, pk: uuid.UUID):
        """
        Xóa một module.
        """
        try:
            module_instance = self.check_module_permission(request, pk)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        try:
            self.module_service.delete_module(module_id=pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # logger.error(...)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InstructorModuleReorderView(CoursePermissionMixin, APIView):
    """
    POST /instructor/courses/<uuid:course_id>/modules/reorder/
    
    Yêu cầu IsInstructor và là chủ sở hữu khóa học.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_service = module_service

    def post(self, request, course_id: uuid.UUID):
        """
        Sắp xếp lại thứ tự các module cho một khóa học.
        """
        try:
            self.check_course_permission(request, course_id)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = ModuleReorderSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            self.module_service.reorder_modules(
                course_id=course_id,
                module_ids=validated_data['module_ids']
            )
            return Response({"detail": "Thứ tự module đã được cập nhật."}, status=status.HTTP_200_OK)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # logger.error(...)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ----------------------------- ADMIN ------------------------------------------------  
class AdminModuleListCreateView(RoleBasedOutputMixin, APIView):
    """
    GET /admin/courses/<uuid:course_id>/modules/
    POST /admin/courses/<uuid:course_id>/modules/
    
    Chỉ dành cho Admin.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    # Admin luôn thấy data admin
    output_dto_public = ModuleAdminOutput 
    output_dto_admin  = ModuleAdminOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_service = module_service 

    def get(self, request, course_id: uuid.UUID):
        """
        Lấy danh sách module (view của Admin).
        """
        try:
            # Admin không cần check quyền, chỉ cần check course tồn tại
            get_course_or_404(course_id) 
        except Http404 as e:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        # Logic lấy data
        try:
            module_domains: list[ModuleDomain] = self.module_service.list_modules_for_course(
                course_id=course_id
            )
            # RoleBasedOutputMixin sẽ dùng ModuleAdminOutput
            return Response({"instance": module_domains}, status=status.HTTP_200_OK)
        except Exception as e: # Service có thể vẫn ném lỗi Dù đã check
            # logger.error(...)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, course_id: uuid.UUID, *args, **kwargs):
        """
        Tạo một module mới (view của Admin).
        """
        try:
            get_course_or_404(course_id)
        except Http404 as e:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        # Logic tạo mới (giống hệt Instructor)
        serializer = ModuleSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            module_create_dto = ModuleInput(**validated_data)
        except ValidationError as e: 
            return Response({"detail": f"Dữ liệu đầu vào không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_module_domain: ModuleDomain = self.module_service.create_module(
                course_id=course_id, 
                data=module_create_dto.to_dict()
            )
            # RoleBasedOutputMixin sẽ dùng ModuleAdminOutput
            return Response(
                {"instance": new_module_domain}, 
                status=status.HTTP_201_CREATED
            )
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # logger.error(...)
            return Response({"detail": "Lỗi không xác định xảy ra trong quá trình tạo module."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminModuleDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /admin/modules/<uuid:pk>/
    PATCH /admin/modules/<uuid:pk>/
    DELETE /admin/modules/<uuid:pk>/
    
    Chỉ dành cho Admin.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    output_dto_public = ModuleAdminOutput
    output_dto_admin  = ModuleAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_service = module_service
        
    def get_object(self, pk: uuid.UUID):
        """
        Hàm helper, chỉ cần lấy instance, không cần join
        (Vì admin không cần check ownership).
        """
        try:
            return Module.objects.get(id=pk)
        except Module.DoesNotExist:
            raise Http404("Module not found.")

    def get(self, request, pk: uuid.UUID):
        """
        Lấy chi tiết một module (view của Admin).
        """
        try:
            # Check tồn tại
            self.get_object(pk) 
            # Lấy domain từ service
            module_domain: ModuleDomain = self.module_service.get_module_by_id(module_id=pk)
            return Response({"instance": module_domain}, status=status.HTTP_200_OK)
        except Http404 as e:
             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # logger.error(...)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, pk: uuid.UUID):
        """
        Cập nhật một phần (partial update) module (view của Admin).
        """
        try:
            module_instance = self.get_object(pk)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        # Logic y hệt Instructor.patch
        serializer = ModuleSerializer(module_instance, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             
        validated_data = serializer.validated_data

        try:
            update_dto = ModuleUpdateInput(**validated_data)
        except ValidationError as e:
            return Response({"detail": f"Dữ liệu đầu vào không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        updates_payload = update_dto.model_dump(exclude_unset=True)

        if not updates_payload:
            module_domain = self.module_service.get_module_by_id(module_id=pk)
            return Response({"instance": module_domain}, status=200)

        try:
            updated_domain: ModuleDomain = self.module_service.update_module(
                module_id=pk, 
                updates=updates_payload
            )
            return Response({"instance": updated_domain}, status=200)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=400)
        except Exception as e:
            # logger.error(...)
            return Response({"detail": "Lỗi không xác định xảy ra trong quá trình cập nhật."}, status=500)

    def delete(self, request, pk: uuid.UUID):
        """
        Xóa một module (view của Admin).
        """
        try:
            # Check tồn tại trước
            self.get_object(pk)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        try:
            self.module_service.delete_module(module_id=pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # logger.error(...)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminModuleReorderView(APIView):
    """
    POST /admin/courses/<uuid:course_id>/modules/reorder/
    
    Chỉ dành cho Admin.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_service = module_service

    def post(self, request, course_id: uuid.UUID):
        """
        Sắp xếp lại thứ tự các module cho một khóa học (view của Admin).
        """
        try:
            get_course_or_404(course_id)
        except Http404 as e:
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
            
        # Logic giống hệt ModuleReorderView.post gốc
        serializer = ModuleReorderSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            self.module_service.reorder_modules(
                course_id=course_id,
                module_ids=validated_data['module_ids']
            )
            return Response({"detail": "Thứ tự module đã được cập nhật."}, status=status.HTTP_200_OK)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # logger.error(...)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 


# class ModuleListCreateView(RoleBasedOutputMixin, APIView):
#     """
#     GET /courses/<uuid:course_id>/modules/
#     POST /courses/<uuid:course_id>/modules/
#     """
#     permission_classes = [permissions.IsAuthenticated, permissions.OR(permissions.IsAdminUser, permissions.AND(IsInstructor, IsCourseOwner))]
    
#     output_dto_public = ModulePublicOutput 
#     output_dto_admin  = ModuleAdminOutput  

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Giả định module_service được inject
#         self.module_service = module_service 

#     def get(self, request, course_id: uuid.UUID):
#         """
#         Lấy danh sách tất cả module cho một khóa học.
#         """
#         try:
#             # Service trả về một list các DOMAIN ENTITIES (ModuleDomain)
#             module_domains: list[ModuleDomain] = self.module_service.list_modules_for_course(
#                 course_id=course_id
#             )
#             return Response({"instance": module_domains}, status=status.HTTP_200_OK)
#         except DomainError as e: # Ví dụ: Course không tìm thấy
#             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             # logger.error(f"Lỗi không xác định khi lấy danh sách module: {e}", exc_info=True)
#             return Response(
#                 {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     def post(self, request, course_id: uuid.UUID, *args, **kwargs):
#         """
#         Tạo một module mới cho khóa học.
#         (Theo cấu trúc của AdminUserListView)
#         """
        
#         # 1. Validate định dạng input thô (dùng DRF Serializer)
#         serializer = ModuleSerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
#         except Exception:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         # 2. Tạo Input DTO từ data đã validate
#         try:
#             # DTO này xử lý validation logic/business (Pydantic)
#             module_create_dto = ModuleInput(**validated_data)
#         except ValidationError as e: # Bắt lỗi validation của Pydantic
#             return Response({"detail": f"Dữ liệu đầu vào không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#         # 3. Gọi Service
#         try:
#             new_module_domain: ModuleDomain = self.module_service.create_module(
#                 course_id=course_id, 
#                 data=module_create_dto.to_dict()
#             )
            
#             return Response(
#                 {"instance": new_module_domain}, 
#                 status=status.HTTP_201_CREATED
#             )
        
#         except DomainError as e: # Bắt lỗi business (ví dụ: "Course không tồn tại")
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
#         except Exception as e:
#             # logger.error(f"Lỗi không xác định khi tạo module: {e}", exc_info=True)
#             return Response({"detail": "Lỗi không xác định xảy ra trong quá trình tạo module."}, 
#                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class ModuleDetailView(RoleBasedOutputMixin, APIView):
#     """
#     GET /modules/<uuid:pk>/
#     PUT /modules/<uuid:pk>/
#     PATCH /modules/<uuid:pk>/
#     DELETE /modules/<uuid:pk>/
#     """
#     permission_classes = [permissions.IsAuthenticated, permissions.OR(permissions.IsAdminUser, permissions.AND(IsInstructor, IsModuleOwner))]
    
#     # output_dto_public = ModulePublicOutput # (Bạn cần định nghĩa)
#     # output_dto_admin  = ModuleAdminOutput  # (Bạn cần định nghĩa)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.module_service = module_service

#     def _get_module_instance(self, pk: uuid.UUID):
#         """Hàm helper để lấy đối tượng Module (Django ORM)."""
#         try:
#             return Module.objects.get(id=pk)
#         except Module.DoesNotExist:
#             raise DomainError("Module không tìm thấy.") # Ném lỗi DomainError
        
#     def get_object(self, pk: uuid.UUID):
#         """
#         Hàm chuẩn của DRF để lấy object.
#         Permission 'IsModuleOwner' sẽ dùng object từ hàm này.
#         """
#         try:
#             module_instance = Module.objects.select_related('course__owner').get(id=pk)
#             return module_instance
#         except Module.DoesNotExist:
#             raise DomainError("Module không tìm thấy.")

#     def get(self, request, pk: uuid.UUID):
#         """
#         Lấy chi tiết một module.
#         """
#         module_instance = self.get_object(pk)
#         self.check_object_permissions(request, module_instance)

#         try:
#             module_domain: ModuleDomain = self.module_service.get_module_by_id(module_id=pk)
#             return Response({"instance": module_domain}, status=status.HTTP_200_OK)
#         except DomainError as e: # Ví dụ: "Module không tìm thấy"
#             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             # logger.error(...)
#             return Response(
#                 {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     def patch(self, request, pk: uuid.UUID):
#         """
#         Cập nhật một phần (partial update) module.
#         (Theo cấu trúc của CurrentUserDetailView)
#         """
#         try:
#             module_instance = self._get_module_instance(pk)
#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

#         # 1. Validate input (dùng DRF Serializer)
#         # Cung cấp 'instance' để serializer có thể xử lý validation (vd: unique)
#         serializer = ModuleSerializer(module_instance, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         validated_data = serializer.validated_data

#         # 2. Tạo Update DTO từ data đã validate
#         try:
#             update_dto = ModuleUpdateInput(**validated_data)
#         except ValidationError as e:
#             return Response({"detail": f"Dữ liệu đầu vào không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#         # 3. Tạo payload update, loại bỏ các giá trị 'None'
#         updates_payload = update_dto.model_dump(exclude_none=True)

#         # Nếu payload rỗng (không có gì thay đổi), trả về instance hiện tại
#         if not updates_payload:
#             module_domain = self.module_service.get_module_by_id(module_id=pk)
#             return Response({"instance": module_domain}, status=200)

#         # 4. Gọi Service
#         try:
#             updated_domain: ModuleDomain = self.module_service.update_module(
#                 module_id=pk, 
#                 updates=updates_payload
#             )
#             return Response({"instance": updated_domain}, status=200)
#         except DomainError as e: # Lỗi business (vd: "Vị trí đã tồn tại")
#             return Response({"detail": str(e)}, status=400)
#         except Exception as e:
#             # logger.error(...)
#             return Response({"detail": "Lỗi không xác định xảy ra trong quá trình cập nhật."}, status=500)

#     def put(self, request, pk: uuid.UUID):
#         """
#         Cập nhật toàn bộ (full update) module.
#         """
#         try:
#             module_instance = self._get_module_instance(pk)
#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
#         # 1. Validate (dùng ModuleCreateSerializer để yêu cầu tất cả các trường)
#         serializer = ModuleCreateSerializer(module_instance, data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
#         except Exception:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#         # 2. Tạo DTO (dùng ModuleInput DTO, không phải UpdateDTO)
#         try:
#             update_dto = ModuleInput(**validated_data)
#         except ValidationError as e:
#             return Response({"detail": f"Dữ liệu đầu vào không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
#         # 3. Gọi Service (payload là dict đầy đủ, không exclude_none)
#         try:
#             updated_domain: ModuleDomain = self.module_service.update_module(
#                 module_id=pk, 
#                 updates=update_dto.to_dict()
#             )
#             return Response({"instance": updated_domain}, status=200)
#         except DomainError as e:
#             return Response({"detail": str(e)}, status=400)
#         except Exception as e:
#             # logger.error(...)
#             return Response({"detail": "Lỗi không xác định xảy ra trong quá trình cập nhật."}, status=500)

#     def delete(self, request, pk: uuid.UUID):
#         """
#         Xóa một module.
#         """
#         try:
#             self.module_service.delete_module(module_id=pk)
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         except DomainError as e: # Ví dụ: "Không tìm thấy"
#             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             # logger.error(...)
#             return Response(
#                 {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class ModuleReorderView(APIView):
#     """
#     POST /courses/<uuid:course_id>/modules/reorder/
#     """
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.module_service = module_service

#     def post(self, request, course_id: uuid.UUID):
#         """
#         Sắp xếp lại thứ tự các module cho một khóa học.
#         Payload mong đợi: {"module_ids": ["uuid1", "uuid2", ...]}
#         """
        
#         # 1. Validate input (dùng serializer tùy chỉnh cho hành động này)
#         serializer = ModuleReorderSerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data # vd: {"module_ids": [...]}
#         except Exception:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         # 2. Không cần DTO vì payload đã đơn giản
        
#         # 3. Gọi Service
#         try:
#             self.module_service.reorder_modules(
#                 course_id=course_id,
#                 module_ids=validated_data['module_ids']
#             )
#             return Response({"detail": "Thứ tự module đã được cập nhật."}, status=status.HTTP_200_OK)
#         except DomainError as e: # Vd: "Số lượng module không khớp", "Module không tìm thấy"
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             # logger.error(...)
#             return Response(
#                 {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
