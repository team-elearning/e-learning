import logging
from django.http import Http404
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied 
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from content.serializers import LessonVersionSerializer, SetStatusSerializer, LessonVersionCreateSerializer, LessonVersionUpdateSerializer
from content.services import lesson_version_service 
from content.api.mixins import RoleBasedOutputMixin, LessonPermissionMixin
from content.api.dtos.lesson_version_dtos import LessonVersionOutput, LessonVersionInput, LessonVersionUpdate, SetStatusInput
from content.services import exceptions as lesson_exceptions
from content.models import LessonVersion
from content.api.permissions import IsInstructor



logger = logging.getLogger(__name__)

# ===================================================================
# ADMIN VIEWS
# ===================================================================

### Admin: List và Create Lesson Versions
class AdminLessonVersionListCreateView(RoleBasedOutputMixin, APIView):
    """
    [Admin]
    GET: Lấy danh sách các phiên bản của một bài học.
    /admin/lessons/<uuid:lesson_id>/versions/
    POST: Tạo một phiên bản mới cho một bài học.
    /admin/lessons/<uuid:lesson_id>/versions/
    """
    permission_classes = [permissions.IsAdminUser]
    
    output_dto_public = LessonVersionOutput
    output_dto_admin = LessonVersionOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_version_service 

    def get(self, request, lesson_id):
        """ [Admin] Lấy danh sách versions cho lesson_id. """
        try:
            versions_list = self.lesson_service.list_versions_for_lesson(
                lesson_id=lesson_id, 
                user=request.user
            )
            return Response({"instance": versions_list}, status=status.HTTP_200_OK)
        except lesson_exceptions.LessonNotFoundError:
            raise Http404("Lesson not found")
        except Exception as e:
            logger.error(f"[Admin] Lỗi khi lấy danh sách versions: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, lesson_id):
        """ [Admin] Tạo một phiên bản mới. """
        serializer = LessonVersionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            create_dto = LessonVersionInput(**validated_data)
            new_version = self.lesson_service.create_lesson_version(
                lesson_id=lesson_id,
                author=request.user,
                data_dto=create_dto
            )
            return Response({"instance": new_version}, status=status.HTTP_201_CREATED)
        except lesson_exceptions.LessonNotFoundError:
            raise Http404("Lesson not found")
        except (lesson_exceptions.DomainError, ValidationError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[Admin] Lỗi khi tạo version: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


### Admin: Chi tiết, Cập nhật, Xóa Lesson Version
class AdminLessonVersionDetailView(RoleBasedOutputMixin, APIView):
    """
    [Admin]
    GET, PUT, PATCH, DELETE cho một LessonVersion cụ thể.
    /admin/lesson-versions/<uuid:pk>/
    """
    permission_classes = [permissions.IsAdminUser] 
    
    output_dto_public = LessonVersionOutput
    output_dto_admin = LessonVersionOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_version_service

    def get_object(self, pk):
        try:
            return LessonVersion.objects.get(pk=pk)
        except LessonVersion.DoesNotExist:
            raise Http404
        
    def get(self, request, pk, *args, **kwargs):
        """ [Admin] Lấy chi tiết một phiên bản. """
        instance = self.get_object(pk)
        return Response({"instance": instance})

    def patch(self, request, pk, *args, **kwargs):
        """ [Admin] Cập nhật một phần (PATCH) một phiên bản. """
        instance = self.get_object(pk)
        serializer = LessonVersionSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        update_dto = LessonVersionUpdate(**validated_data)
        updates_payload = update_dto.model_dump(exclude_unset=True)
            
        if not updates_payload:
            return Response({"instance": instance}, status=status.HTTP_200_OK)

        try:
            updated_version = self.lesson_service.update_lesson_version(
                version_id=pk, 
                user=request.user,
                updates=updates_payload
            )
            return Response({"instance": updated_version}, status=status.HTTP_200_OK)
        except (lesson_exceptions.DomainError, ValidationError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[Admin] Lỗi khi cập nhật version {pk}: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk, *args, **kwargs):
        """ [Admin] Xóa một phiên bản. """
        instance = self.get_object(pk)
        try:
            self.lesson_service.delete_lesson_version(
                version_id=instance.id, 
                user=request.user
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except lesson_exceptions.DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[Admin] Lỗi khi xóa version {pk}: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


### Admin: Cập nhật Trạng thái (Set Status)
class AdminLessonVersionSetStatusView(APIView):
    """
    [Admin]
    Action tùy chỉnh để thay đổi 'status' của một phiên bản.
    /admin/lesson-versions/<uuid:pk>/set_status/
    """
    permission_classes = [permissions.IsAdminUser] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_version_service

    def post(self, request, pk):
        serializer = SetStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        try:
            status_dto = SetStatusInput(**validated_data)
            updated_version = self.lesson_service.set_version_status(
                version_id=pk,
                user=request.user,
                new_status=status_dto.status
            )
            return Response({"instance": updated_version}, status=status.HTTP_200_OK)
        except lesson_exceptions.VersionNotFoundError:
            raise Http404("LessonVersion not found")
        except lesson_exceptions.DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[Admin] Lỗi khi set_status cho version {pk}: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===================================================================
# INSTRUCTOR (OWNER) VIEWS
# ===================================================================
class InstructorLessonVersionListCreateView(RoleBasedOutputMixin, APIView, LessonPermissionMixin):
    """
    [Instructor]
    GET: Lấy danh sách các phiên bản của một bài học.
    /instructor/lessons/<uuid:lesson_id>/versions/
    POST: Tạo một phiên bản mới cho một bài học.
    /instructor/lessons/<uuid:lesson_id>/versions/
    Sử dụng LessonPermissionMixin để kiểm tra quyền sở hữu.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor] # Yêu cầu đăng nhập
    
    output_dto_public = LessonVersionOutput
    output_dto_admin = LessonVersionOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_version_service 

    def get(self, request, lesson_id):
        """ [Instructor] Lấy danh sách versions cho lesson_id. """
        try:
            # KIỂM TRA QUYỀN TRƯỚC
            self.check_lesson_permission(request, lesson_id)
            
            versions_list = self.lesson_service.list_versions_for_lesson(
                lesson_id=lesson_id, 
                user=request.user
            )
            return Response({"instance": versions_list}, status=status.HTTP_200_OK)
        except (Http404, lesson_exceptions.LessonNotFoundError):
            raise Http404("Bài học không tìm thấy.")
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"[Instructor] Lỗi khi lấy danh sách versions: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, lesson_id):
        """ [Instructor] Tạo một phiên bản mới. """
        try:
            # KIỂM TRA QUYỀN TRƯỚC
            # (check_lesson_permission trả về lesson, nhưng ta chưa cần dùng)
            self.check_lesson_permission(request, lesson_id)
        except Http404:
            raise Http404("Bài học không tìm thấy.")
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        # Nếu có quyền, tiếp tục xử lý
        serializer = LessonVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            create_dto = LessonVersionInput(**validated_data)
            new_version = self.lesson_service.create_lesson_version(
                lesson_id=lesson_id,
                author=request.user,
                data_dto=create_dto
            )
            return Response({"instance": new_version}, status=status.HTTP_201_CREATED)
        except (lesson_exceptions.DomainError, ValidationError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[Instructor] Lỗi khi tạo version: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


### Instructor: Chi tiết, Cập nhật, Xóa Lesson Version
class InstructorLessonVersionDetailView(RoleBasedOutputMixin, APIView, LessonPermissionMixin):
    """
    [Instructor]
    GET /instructor/lesson-versions/<uuid:pk>/
    GET, PUT, PATCH, DELETE cho một LessonVersion cụ thể.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor] # Yêu cầu đăng nhập
    
    output_dto_public = LessonVersionOutput
    output_dto_admin = LessonVersionOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_version_service

    def get_object_and_check_perm(self, request, pk):
        """
        Helper: Lấy LessonVersion và kiểm tra quyền sở hữu Lesson.
        """
        try:
            instance = LessonVersion.objects.select_related('lesson').get(pk=pk)
        except LessonVersion.DoesNotExist:
            raise Http404("Phiên bản bài học không tìm thấy.")
        
        # Lấy lesson_id từ instance và gọi mixin kiểm tra quyền
        if not instance.lesson_id:
             raise Http404("Phiên bản này không liên kết với bài học nào.")
             
        self.check_lesson_permission(request, instance.lesson_id)
        
        return instance
        
    def get(self, request, pk, *args, **kwargs):
        """ [Instructor] Lấy chi tiết một phiên bản. """
        try:
            instance = self.get_object_and_check_perm(request, pk)
            return Response({"instance": instance})
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

    def patch(self, request, pk, *args, **kwargs):
        """ [Instructor] Cập nhật một phần (PATCH) một phiên bản. """
        try:
            instance = self.get_object_and_check_perm(request, pk)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        # Nếu có quyền, tiếp tục xử lý
        serializer = LessonVersionUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        update_dto = LessonVersionUpdate(**validated_data)
        updates_payload = update_dto.model_dump(exclude_unset=True)
            
        if not updates_payload:
            return Response({"instance": instance}, status=status.HTTP_200_OK)

        try:
            updated_version = self.lesson_service.update_lesson_version(
                version_id=pk, 
                user=request.user,
                updates=updates_payload
            )
            return Response({"instance": updated_version}, status=status.HTTP_200_OK)
        except (lesson_exceptions.DomainError, ValidationError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[Instructor] Lỗi khi cập nhật version {pk}: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk, *args, **kwargs):
        """ [Instructor] Xóa một phiên bản. """
        try:
            instance = self.get_object_and_check_perm(request, pk)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
        # Nếu có quyền, tiếp tục xử lý
        try:
            self.lesson_service.delete_lesson_version(
                version_id=instance.id, 
                user=request.user
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except lesson_exceptions.DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[Instructor] Lỗi khi xóa version {pk}: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


### Instructor: Cập nhật Trạng thái (Set Status)
class InstructorLessonVersionSetStatusView(APIView, LessonPermissionMixin):
    """
    [Instructor]
    Action tùy chỉnh để thay đổi 'status' của một phiên bản.
    POST /instructor/lesson-versions/<uuid:pk>/set_status/
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor] # Yêu cầu đăng nhập

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_version_service

    def post(self, request, pk):
        try:
            # Lấy object trước để có lesson_id
            try:
                instance = LessonVersion.objects.select_related('lesson').get(pk=pk)
            except LessonVersion.DoesNotExist:
                raise Http404("Phiên bản bài học không tìm thấy.")
            
            # Kiểm tra quyền
            self.check_lesson_permission(request, instance.lesson_id)
        
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        # Nếu có quyền, tiếp tục xử lý
        serializer = SetStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        try:
            status_dto = SetStatusInput(**validated_data)
            updated_version = self.lesson_service.set_version_status(
                version_id=pk,
                user=request.user,
                new_status=status_dto.status
            )
            return Response({"instance": updated_version}, status=status.HTTP_200_OK)
        except lesson_exceptions.DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[Instructor] Lỗi khi set_status cho version {pk}: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
