import logging
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from pydantic import ValidationError as PydanticValidationError
from django.http import Http404

from content import models
from content.serializers import CourseSerializer, CourseCreateSerializer
from content.services import course_service     
from content.api.dtos.course_dto import CoursePublicOutput, CourseAdminOutput, CourseCreateInput, CourseUpdateInput
from content.services.exceptions import DomainError, ValidationError as DRFValidationError    
from content.api.permissions import IsInstructor
from content.api.mixins import RoleBasedOutputMixin, CoursePermissionMixin
from content.services.exceptions import InvalidOperation



logger = logging.getLogger(__name__)
class PublicCourseListView(RoleBasedOutputMixin, APIView):
    """
    GET /courses/ - List tất cả courses (public).
    """
    # IsAuthenticated: Phải đăng nhập
    # IsAllowAny: Ai cũng thấy (thay thế nếu cần)
    permission_classes = [permissions.IsAuthenticated] 

    # Cấu hình DTO output
    output_dto_public = CoursePublicOutput
    output_dto_admin  = CoursePublicOutput # Luôn là public

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, *args, **kwargs):
        """
        Xử lý GET request để list tất cả courses.
        """
        try:
            courses_list = self.course_service.list_courses()
            return Response({"instance": courses_list}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Lỗi trong PublicCourseListView (GET): {e}", exc_info=True)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PublicCourseDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /api/v1/courses/<pk>/ - Lấy chi tiết course (public).
    """
    permission_classes = [permissions.IsAuthenticated]

    # Cấu hình DTO output
    output_dto_public = CoursePublicOutput
    output_dto_admin  = CoursePublicOutput # Luôn là public

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        Xử lý GET request để lấy chi tiết một course.
        """
        try:
            course = self.course_service.get_course_by_id(course_id=pk)
            return Response({"instance": course}, status=status.HTTP_200_OK)
        
        except DomainError as e: # Lỗi "Not Found"
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Lỗi trong PublicCourseDetailView (GET): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CourseEnrollView(APIView):
    """
    POST /courses/{id}/enroll/ -> enroll current user
    DELETE /courses/{id}/enroll/ -> unenroll
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id: str):
        try:
            course = course_service.get_course(course_id)
            if not course:
                return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
            # This feature might not be fully implemented in the service
            if hasattr(course_service, 'enroll_user'):
                course_service.enroll_user(course_id=course_id, user_id=request.user.id)
                return Response({"success": True}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Enroll feature not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception as ex:
            return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id: str):
        try:
            if hasattr(course_service, 'unenroll_user'):
                course_service.unenroll_user(course_id=course_id, user_id=request.user.id)
                return Response({"success": True}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Unenroll feature not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception as ex:
            return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


# ------------------ ADMIN -------------------------------
class AdminCourseListCreateView(RoleBasedOutputMixin, APIView):
    """
    GET /admin/courses/ - List courses (cho Admin).
    POST /admin/courses/ - Tạo course mới (cho Admin).
    """
    permission_classes = [permissions.IsAdminUser] # CHỈ Admin

    # Cấu hình DTO output
    output_dto_public = CoursePublicOutput 
    output_dto_admin  = CourseAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, *args, **kwargs):
        """ Lấy list (bản
        admin) """
        try:
            courses_list = self.course_service.list_courses()
            return Response({"instance": courses_list}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Lỗi trong AdminCourseListCreateView (GET): {e}", exc_info=True)
            return Response({"detail": f"Đã xảy ra lỗi: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        """ Tạo course mới (logic y hệt) """
        
        # 1. Validate DRF (nhớ sửa lỗi import)
        serializer = CourseCreateSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError: # Đã sửa
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Tạo Pydantic DTO (nhớ sửa lỗi import)
        try:
            course_create_dto = CourseCreateInput(**validated_data)
        except PydanticValidationError as e: # Đã sửa
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Gọi service
        try:
            new_course = self.course_service.create_course(
                data=course_create_dto.model_dump(),
                owner=request.user
            )
            return Response({"instance": new_course}, status=status.HTTP_201_CREATED)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong AdminCourseListCreateView (POST): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi tạo course."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminCourseDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /admin/courses/<pk>/    - Lấy chi tiết (cho Admin).
    PATCH /admin/courses/<pk>/  - Cập nhật một phần (cho Admin).
    DELETE /admin/courses/<pk>/ - Xoá course (cho Admin).
    """
    permission_classes = [permissions.IsAdminUser] # CHỈ Admin

    # Cấu hình DTO output
    output_dto_public = CourseAdminOutput # Luôn là admin
    output_dto_admin  = CourseAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Lấy chi tiết (bản admin) """
        try:
            course = self.course_service.get_course_by_id(course_id=pk)
            return Response({"instance": course}, status=status.HTTP_200_OK)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Lỗi trong AdminCourseDetailView (GET): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Cập nhật  """
        try:
            instance = self.course_service.get_course_by_id(course_id=pk)
        except DomainError as e:
            return Response({"detail": f"Không tìm thấy course: {e}"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseSerializer(instance, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError: # Đã sửa
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            update_dto = CourseUpdateInput(**validated_data)
            updates_payload = update_dto.model_dump(exclude_none=True)
        except PydanticValidationError as e: # Đã sửa
             return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        if not updates_payload:
            return Response({"instance": instance}, status=status.HTTP_200_OK)

        try:
            updated_course = self.course_service.update_course(
                course_id=pk,
                updates=updates_payload
            )
            return Response({"instance": updated_course}, status=status.HTTP_200_OK)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong AdminCourseDetailView (PATCH): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi cập nhật course."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Xóa (logic y hệt) """
        try:
            self.course_service.delete_course(course_id=pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Lỗi trong AdminCourseDetailView (DELETE): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi xoá course."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminCoursePublishView(RoleBasedOutputMixin, APIView):
    """
    POST /courses/{id}/publish/
    body: {"require_all_lessons_published": false}
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request, course_id: str):
        require_all = request.data.get("require_all_lessons_published", False)
        course_domain = course_service.get_course(course_id)
        if not course_domain:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            # Using a simple dict as command for simplicity, matching service layer
            publish_command_data = {"published": True, "require_all_lessons_published": require_all}
            course_domain = course_service.publish_course(course_id=course_id, publish_data=type("PublishCmd", (), publish_command_data))
            
            return Response(course_domain)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class AdminCourseUnpublishView(RoleBasedOutputMixin, APIView):
    """
    POST /courses/{id}/unpublish/
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def post(self, request, course_id: str):
        try:
            updated = course_service.unpublish_course(course_id=course_id)
            if not updated:
                return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(updated)
        except Exception as ex:
            return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


# ------------------ INSTRUCTOR --------------------
class InstructorCourseListCreateView(RoleBasedOutputMixin, APIView):
    """
    GET /instructor/courses/ - List các course CỦA TÔI.
    POST /instructor/courses/ - Tạo course mới (owner là TÔI).
    """
    permission_classes = [IsInstructor] # Chỉ Instructor mới được vào

    # Instructor cũng thấy DTO admin cho course của mình
    output_dto_public = CoursePublicOutput
    output_dto_admin  = CourseAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, *args, **kwargs):
        """ Lấy list course CỦA TÔI """
        try:
            courses_list = self.course_service.list_courses_for_instructor(owner=request.user)
            return Response({"instance": courses_list}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Lỗi trong InstructorCourseListCreateView (GET): {e}", exc_info=True)
            return Response({"detail": f"Đã xảy ra lỗi: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request, *args, **kwargs):
        """ Tạo course mới (logic y hệt Admin post) """
        
        serializer = CourseCreateSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            course_create_dto = CourseCreateInput(**validated_data)
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Gọi hàm create_course chung, vì owner đã được truyền vào
            new_course = self.course_service.create_course(
                data=course_create_dto.model_dump(),
                owner=request.user
            )
            return Response({"instance": new_course}, status=status.HTTP_201_CREATED)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong InstructorCourseListCreateView (POST): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi tạo course."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InstructorCourseDetailView(RoleBasedOutputMixin, CoursePermissionMixin, APIView):
    """
    GET /instructor/courses/<pk>/    - Lấy chi tiết (của tôi).
    PATCH /instructor/courses/<pk>/  - Cập nhật (của tôi).
    DELETE /instructor/courses/<pk>/ - Xoá (của tôi).
    """
    # Phải là Instructor 
    permission_classes = [IsInstructor] 

    output_dto_public = CourseAdminOutput
    output_dto_admin  = CourseAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Lấy chi tiết """
        try:
            # 1. Kiểm tra quyền (Admin hoặc Owner)
            self.check_course_permission(request, course_id=pk)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Gọi hàm service mới
            course = self.course_service.get_course_by_id_for_instructor(
                course_id=pk, owner=request.user
            )
            return Response({"instance": course}, status=status.HTTP_200_OK)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": f"Lỗi không xác định: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def patch(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Cập nhật (đã check quyền sở hữu) """
        try:
            # Kiểm tra quyền VÀ lấy instance
            course_instance = self.check_course_permission(request, course_id=pk)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        
        # Validate 
        try:
            instance = self.course_service.get_course_by_id_for_instructor(
                course_id=pk, owner=request.user
            )
        except DomainError as e:
            return Response({"detail": f"Không tìm thấy course: {e}"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseSerializer(instance, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            update_dto = CourseUpdateInput(**validated_data)
            updates_payload = update_dto.model_dump(exclude_none=True)
        except PydanticValidationError as e:
             return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        if not updates_payload:
            return Response({"instance": instance}, status=status.HTTP_200_OK)

        # Gọi service 
        try:
            updated_course = self.course_service.update_course_for_instructor(
                course_id=pk,
                updates=updates_payload,
                owner=request.user
            )
            return Response({"instance": updated_course}, status=status.HTTP_200_OK)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Xóa """
        try:
            # Kiểm tra quyền
            self.check_course_permission(request, course_id=pk)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            self.course_service.delete_course_for_instructor(
                course_id=pk, owner=request.user
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        

class InstructorCoursePublishView(APIView):
    """
    POST /instructor/courses/{id}/publish/
    """
    permission_classes = [IsInstructor] 

    def post(self, request, course_id: str):
        try:
            # Kiểm tra quyền
            self.check_course_permission(request, course_id=course_id)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        
        require_all = request.data.get("require_all_lessons_published", False)
        
        try:
            publish_command_data = {"published": True, "require_all_lessons_published": require_all}
            
            # Gọi service mới của Instructor
            course_domain = course_service.publish_course_for_instructor(
                course_id=course_id, 
                publish_data=type("PublishCmd", (), publish_command_data),
                owner=request.user
            )
            
            # Trả về DTO (thay vì Serializer)
            return Response(course_domain, status=status.HTTP_200_OK)

        except (DomainError, InvalidOperation) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class InstructorCourseUnpublishView(APIView):
    """
    POST /api/v1/instructor/courses/{id}/unpublish/
    """
    permission_classes = [IsInstructor]

    def post(self, request, course_id: str):
        try:
            # Kiểm tra quyền
            self.check_course_permission(request, course_id=course_id)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Gọi service mới của Instructor
            course_domain = course_service.unpublish_course_for_instructor(
                course_id=course_id,
                owner=request.user
            )
            
            if not course_domain:
                 return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

            return Response(CourseAdminOutput.model_validate(course_domain).model_dump(), status=status.HTTP_200_OK)
            
        except (DomainError, InvalidOperation) as ex:
            return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)
