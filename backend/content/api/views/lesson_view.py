import logging
import uuid
from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from content.models import Lesson, Module
from content.services import lesson_service 
from core import exceptions 
from core.api.permissions import IsInstructor
from content.api.dtos.lesson_dto import LessonInput, LessonUpdateInput, LessonReorderInput, LessonPublicOutput, LessonAdminOutput
from content.serializers import LessonSerializer
from content.domains.lesson_domain import LessonDomain
from core.api.mixins import RoleBasedOutputMixin, ModulePermissionMixin, LessonPermissionMixin
from core.exceptions import DomainError



logger = logging.getLogger(__name__)

# Helper để kiểm tra sự tồn tại của Module
def get_module_or_404(module_id: uuid.UUID):
    try:
        return Module.objects.get(pk=module_id)
    except Module.DoesNotExist:
        raise Http404("Module not found.")


class PublicLessonListView(RoleBasedOutputMixin, APIView):
    """
    GET /modules/<uuid:module_id>/lessons/ (Public)
    """
    permission_classes = [permissions.IsAuthenticated]

    output_dto_public = LessonPublicOutput
    output_dto_admin = LessonAdminOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_service

    def get(self, request, module_id, *args, **kwargs):
        """
        Handles GET requests to list all lessons for a specific module.
        """
        try:
            lesson_domains: list[LessonDomain] = self.lesson_service.list_lessons_for_module(
                module_id=module_id
            )
            return Response({"instance": lesson_domains}, status=status.HTTP_200_OK)
        
        except exceptions.ModuleNotFoundError:
            return Response({"detail": "Module not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error listing lessons: {e}", exc_info=True)
            return Response(
                {"detail": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PublicLessonDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /lessons/<uuid:pk>/
    """
    permission_classes = [permissions.IsAuthenticated]

    output_dto_public = LessonPublicOutput
    output_dto_admin = LessonAdminOutput 

    def get_object(self, pk):
        try:
            return Lesson.objects.get(pk=pk)
        except Lesson.DoesNotExist:
            raise Http404("Lesson not found.")
    
    def get(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        
        try:
            lesson_domain = LessonDomain.from_model(instance)
        except Exception as e:
            logger.error(f"Lỗi khi convert Lesson model sang domain: {e}", exc_info=True)
            return Response(
                {"detail": "Lỗi khi xử lý dữ liệu bài học."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({"instance": lesson_domain})


### -------- INSTRUCTOR ----------------
class InstructorLessonListView(RoleBasedOutputMixin, ModulePermissionMixin, APIView):
    """
    GET /instructor/modules/<uuid:module_id>/lessons/
    POST /instructor/modules/<uuid:module_id>/lessons/
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor] 

    output_dto_public = LessonPublicOutput
    output_dto_admin = LessonAdminOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_service

    def get(self, request, module_id, *args, **kwargs):
        """
        Handles GET requests to list all lessons for a specific module.
        (Instructor/Admin view - returns detailed admin data)
        """
        try:
            # Kiểm tra quyền sở hữu module
            self.check_module_permission(request, module_id)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        # Nếu có quyền, lấy danh sách
        try:
            lesson_domains: list[LessonDomain] = self.lesson_service.list_lessons_for_module(
                module_id=module_id
            )
            return Response({"instance": lesson_domains}, status=status.HTTP_200_OK)
        
        except exceptions.ModuleNotFoundError:
            return Response({"detail": "Module not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error listing lessons for instructor: {e}", exc_info=True)
            return Response(
                {"detail": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, module_id, *args, **kwargs):
        """
        Handles POST requests to create a new lesson.
        """
        try:
            # Hàm này đến từ ModulePermissionMixin, kiểm tra user có phải owner/admin
            module_instance = self.check_module_permission(request, module_id)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        serializer = LessonSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create Input DTO (Pydantic)
        try:
            lesson_create_dto = LessonInput(**validated_data)
        except Exception as e: 
            return Response({"detail": f"Invalid input data: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Call the service
        try:
            new_lesson_domain: LessonDomain = self.lesson_service.create_lesson(
                module_id=module_id, 
                data=lesson_create_dto.to_dict()
            )
            return Response(
                {"instance": new_lesson_domain}, 
                status=status.HTTP_201_CREATED
            )
        
        except exceptions.ModuleNotFoundError:
            return Response({"detail": "Module not found."}, status=status.HTTP_404_NOT_FOUND)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in InstructorLessonListView (POST): {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred during lesson creation."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class InstructorLessonDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /instructor/lessons/<uuid:pk>/
    PATCH /instructor/lessons/<uuid:pk>/
    DELETE /instructor/lessons/<uuid:pk>/
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    output_dto_public = LessonPublicOutput
    output_dto_admin = LessonAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_service

    def get_object(self, pk):
        try:
            return Lesson.objects.select_related('module__course__owner').get(pk=pk)
        except Lesson.DoesNotExist:
            raise Http404("Lesson not found.")
    
    def get(self, request, pk, *args, **kwargs):
        """
        Handles GET requests for instructors/admins.
        """
        instance = self.get_object(pk)
        self.check_object_permissions(request, instance) 
        
        try:
            lesson_domain = LessonDomain.from_model(instance)
        except Exception as e:
            logger.error(f"Lỗi khi convert Lesson model sang domain: {e}", exc_info=True)
            return Response(
                {"detail": "Lỗi khi xử lý dữ liệu bài học."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        return Response({"instance": lesson_domain})

    def patch(self, request, pk, *args, **kwargs):
        """
        Handles PATCH requests.
        """
        instance = self.get_object(pk)
        self.check_object_permissions(request, instance) 
        
        serializer = LessonSerializer(instance, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            lesson_update_dto = LessonUpdateInput(**validated_data)
            updates_payload = lesson_update_dto.model_dump(exclude_unset=True)
            
            if not updates_payload:
                lesson_domain = LessonDomain.from_model(instance)
                return Response({"instance": lesson_domain}, status=status.HTTP_200_OK)

            updated_domain = self.lesson_service.update_lesson(
                lesson_id=instance.id, 
                updates=updates_payload
            )
            return Response({"instance": updated_domain}, status=status.HTTP_200_OK)
        except (ValidationError, DomainError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in InstructorLessonDetailView (PATCH): {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk, *args, **kwargs):
        """
        Handles DELETE requests.
        """
        instance = self.get_object(pk)
        # Kiểm tra quyền (DRF tự động làm)
        self.check_object_permissions(request, instance)
        
        try:
            self.lesson_service.delete_lesson(lesson_id=instance.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in InstructorLessonDetailView (DELETE): {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstructorLessonReorderView(ModulePermissionMixin, APIView):
    """
    POST /instructor/modules/<uuid:module_id>/lessons/reorder/
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_service

    def post(self, request, module_id, *args, **kwargs):
        """
        Handles POST requests to reorder lessons.
        """
        try:
            self.check_module_permission(request, module_id)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = LessonSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            reorder_dto = LessonReorderInput(**validated_data)

            self.lesson_service.reorder_lessons(
                module_id=module_id,
                lesson_ids=reorder_dto.lesson_ids
            )
            return Response({"detail": "Lessons reordered successfully."}, status=status.HTTP_200_OK)
        except exceptions.ModuleNotFoundError:
            return Response({"detail": "Module not found."}, status=status.HTTP_404_NOT_FOUND)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in InstructorLessonReorderView (POST): {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred during reordering."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# ----------- ADMIN --------------------------
class AdminModuleLessonView(RoleBasedOutputMixin, APIView):
    """
    GET /admin/modules/<uuid:module_id>/lessons/
    POST /admin/modules/<uuid:module_id>/lessons/
    
    View cho admin để list hoặc tạo lesson cho một module cụ thể.
    """
    permission_classes = [permissions.IsAdminUser] # Chỉ admin

    # Admin luôn thấy data admin
    output_dto_public = LessonAdminOutput
    output_dto_admin = LessonAdminOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_service

    def get(self, request, module_id, *args, **kwargs):
        """
        Handles GET requests to list all lessons for a specific module (Admin view).
        """
        try:
            # Đảm bảo module tồn tại trước khi list
            get_module_or_404(module_id) 
            
            lesson_domains: list[LessonDomain] = self.lesson_service.list_lessons_for_module(
                module_id=module_id
            )
            # RoleBasedOutputMixin sẽ tự động dùng LessonAdminOutput cho admin
            return Response({"instance": lesson_domains}, status=status.HTTP_200_OK)
        
        except Http404:
            return Response({"detail": "Module not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error listing lessons for admin (module_id: {module_id}): {e}", exc_info=True)
            return Response(
                {"detail": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, module_id, *args, **kwargs):
        """
        Handles POST requests to create a new lesson (Admin view).
        Admin không cần check permission sở hữu.
        """
        try:
            # Chỉ cần kiểm tra module tồn tại
            get_module_or_404(module_id)
        except Http404 as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = LessonSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create Input DTO (Pydantic)
        try:
            lesson_create_dto = LessonInput(**validated_data)
        except Exception as e: 
            return Response({"detail": f"Invalid input data: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Call the service
        try:
            new_lesson_domain: LessonDomain = self.lesson_service.create_lesson(
                module_id=module_id, 
                data=lesson_create_dto.to_dict()
            )
            # RoleBasedOutputMixin sẽ tự động dùng LessonAdminOutput
            return Response(
                {"instance": new_lesson_domain}, 
                status=status.HTTP_201_CREATED
            )
        
        except exceptions.ModuleNotFoundError: # Mặc dù đã check, service có thể check lại
            return Response({"detail": "Module not found."}, status=status.HTTP_404_NOT_FOUND)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in AdminModuleLessonView (POST): {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred during lesson creation."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminLessonListView(RoleBasedOutputMixin, APIView):
    """
    GET /admin/lessons/
    View cho admin để list *tất cả* lesson trong hệ thống.
    """
    permission_classes = [permissions.IsAdminUser]
    
    # Admin luôn thấy data của admin
    output_dto_public = LessonAdminOutput
    output_dto_admin = LessonAdminOutput

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to list all lessons in the system for admins.
        """
        try:
            # Giả sử admin muốn xem tất cả, có thể thêm phân trang sau
            all_lessons = Lesson.objects.all().order_by('-created_at')
            
            # Chúng ta không có service layer cho "list all", 
            # nên sẽ convert thủ công giống DetailView
            lesson_domains = []
            for lesson in all_lessons:
                lesson_domains.append(LessonDomain.from_model(lesson))
                
            return Response({"instances": lesson_domains}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error listing all lessons for admin: {e}", exc_info=True)
            return Response(
                {"detail": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class AdminLessonDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /admin/lessons/<uuid:pk>/
    PATCH /admin/lessons/<uuid:pk>/
    DELETE /admin/lessons/<uuid:pk>/
    
    View cho admin để quản lý *bất kỳ* lesson nào.
    """
    permission_classes = [permissions.IsAdminUser] # Chỉ admin

    output_dto_public = LessonPublicOutput
    output_dto_admin = LessonAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_service = lesson_service

    def get_object(self, pk):
        try:
            # Admin không cần select_related để check perm, nhưng để data đầy đủ thì tốt
            return Lesson.objects.select_related('module__course__owner').get(pk=pk)
        except Lesson.DoesNotExist:
            raise Http404("Lesson not found.")
    
    def get(self, request, pk, *args, **kwargs):
        """
        Admin GET: Không cần check_object_permissions
        """
        instance = self.get_object(pk)
        # Bỏ qua self.check_object_permissions(request, instance)
        
        try:
            lesson_domain = LessonDomain.from_model(instance)
        except Exception as e:
            logger.error(f"Lỗi khi convert Lesson model sang domain (Admin): {e}", exc_info=True)
            return Response(
                {"detail": "Lỗi khi xử lý dữ liệu bài học."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        return Response({"instance": lesson_domain})

    def patch(self, request, pk, *args, **kwargs):
        """
        Admin PATCH: Không cần check_object_permissions
        """
        instance = self.get_object(pk)
        # Bỏ qua self.check_object_permissions(request, instance)
        
        serializer = LessonSerializer(instance, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            lesson_update_dto = LessonUpdateInput(**validated_data)
            updates_payload = lesson_update_dto.model_dump(exclude_unset=True)
            
            if not updates_payload:
                lesson_domain = LessonDomain.from_model(instance)
                return Response({"instance": lesson_domain}, status=status.HTTP_200_OK)

            updated_domain = self.lesson_service.update_lesson(
                lesson_id=instance.id, 
                updates=updates_payload
            )
            return Response({"instance": updated_domain}, status=status.HTTP_200_OK)
        except (ValidationError, DomainError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in AdminLessonDetailView (PATCH): {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk, *args, **kwargs):
        """
        Admin DELETE: Không cần check_object_permissions
        """
        instance = self.get_object(pk)
        # Bỏ qua self.check_object_permissions(request, instance)
        
        try:
            self.lesson_service.delete_lesson(lesson_id=instance.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in AdminLessonDetailView (DELETE): {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# ----------------------------------- LESSON CONTENT -----------------------------------------------------
class LessonContentView(RoleBasedOutputMixin, APIView):
    """
    GET /lessons/<uuid:lesson_id>/content/

    API công khai cho người học (player) đã ghi danh.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    # Người học chỉ thấy output public
    output_dto_public = LessonPublicOutput
    output_dto_admin = LessonAdminOutput 

    def get(self, request, lesson_id):
        """
        Xử lý request GET để lấy nội dung bài học đã published.
        
        TRÁCH NHIỆM PHÂN CHIA:
        - View: Chỉ kiểm tra user đã login (IsAuthenticated).
        - Service: Kiểm tra nghiệp vụ (đã ghi danh, bài học đã publish,...)
        """
        try:
            # 1. Ủy quyền toàn bộ logic nghiệp vụ cho service
            # Service sẽ kiểm tra tất cả:
            # - Lesson có tồn tại không?
            # - User có 'enrolled' không?
            # - Có 'LessonVersion' nào status='published' không?
            published_version_domain = lesson_service.get_published_lesson_content(
                user=request.user, 
                lesson_id=lesson_id
            )
            
            # 2. Trả về domain object, RoleBasedOutputMixin sẽ lo phần serialization
            return Response({"instance": published_version_domain}, status=status.HTTP_200_OK)

        except exceptions.LessonNotFoundError:
            return Response(
                {"detail": "Không tìm thấy bài học."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        except exceptions.NotEnrolledError:
            return Response(
                {"detail": "Bạn phải ghi danh vào khóa học để xem nội dung này."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        except exceptions.NoPublishedContentError:
            return Response(
                {"detail": "Bài học này chưa có nội dung được xuất bản."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        except Exception as e:
            logger.error(
                f"Lỗi không xác định khi lấy nội dung bài học (content view) {lesson_id}: {e}", 
                exc_info=True
            )
            return Response(
                {"detail": "Lỗi hệ thống, không thể tải nội dung bài học."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# --- API cho Quản trị viên (Admin) ---

class AdminLessonPreviewView(RoleBasedOutputMixin, APIView):
    """
    GET /admin/lessons/<uuid:lesson_id>/preview/
    
    API nội bộ cho Admin xem trước (preview) bản nháp (draft).
    Luôn trả về phiên bản (version) MỚI NHẤT.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    # Admin luôn thấy output admin
    output_dto_public = LessonPublicOutput
    output_dto_admin = LessonAdminOutput

    def get(self, request, lesson_id):
        """
        TRÁCH NHIỆM PHÂN CHIA:
        - View: Kiểm tra user là Admin (IsAdminUser).
        - Service: Lấy phiên bản mới nhất của bài học.
        """
        try:
            # 1. Ủy quyền logic "lấy bản mới nhất" cho service
            # Vì đã là Admin, không cần kiểm tra quyền sở hữu
            latest_version_domain = lesson_service.get_lesson_preview(
                lesson_id=lesson_id
            )

            # 2. Trả về domain object
            return Response({"instance": latest_version_domain}, status=status.HTTP_200_OK)

        except exceptions.LessonNotFoundError:
            return Response(
                {"detail": "Không tìm thấy bài học."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        except exceptions.VersionNotFoundError:
            return Response(
                {"detail": "Bài học này chưa có bất kỳ phiên bản nội dung nào."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        except Exception as e:
            logger.error(
                f"Lỗi không xác định khi Admin lấy (preview view) {lesson_id}: {e}", 
                exc_info=True
            )
            return Response(
                {"detail": "Lỗi hệ thống, không thể tải nội dung xem trước."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# --- API cho Tác giả (Instructor/Owner) ---

class InstructorLessonPreviewView(RoleBasedOutputMixin, LessonPermissionMixin, APIView):
    """
    GET /instructor/lessons/<uuid:lesson_id>/preview/
    
    API cho Instructor (Owner) xem trước bản nháp.
    Luôn trả về phiên bản MỚI NHẤT.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor]
    
    # Instructor cũng được xem như Admin về mặt hiển thị dữ liệu
    output_dto_public = LessonPublicOutput
    output_dto_admin = LessonAdminOutput

    def get(self, request, lesson_id):
        """
        TRÁCH NHIỆM PHÂN CHIA:
        - View: Kiểm tra user là Owner (dùng LessonPermissionMixin).
        - Service: Lấy phiên bản mới nhất của bài học.
        """
        try:
            # 1. Kiểm tra quyền sở hữu (View Layer)
            # Sẽ raise 404 hoặc 403 nếu không đạt
            self.check_lesson_permission(request, lesson_id)
            
            # 2. Ủy quyền logic "lấy bản mới nhất" cho service
            latest_version_domain = lesson_service.get_lesson_preview(
                lesson_id=lesson_id
            )

            # 3. Trả về domain object
            return Response({"instance": latest_version_domain}, status=status.HTTP_200_OK)

        except (Http404, PermissionDenied) as e:
            # Bắt lỗi 404, 403 từ mixin
            return Response({"detail": str(e)}, status=e.status_code)

        except exceptions.LessonNotFoundError:
            # Lỗi 404 từ service (dự phòng)
            return Response(
                {"detail": "Không tìm thấy bài học."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        except exceptions.VersionNotFoundError:
            return Response(
                {"detail": "Bài học này chưa có bất kỳ phiên bản nội dung nào."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        except Exception as e:
            logger.error(
                f"Lỗi không xác định khi Instructor lấy (preview view) {lesson_id}: {e}", 
                exc_info=True
            )
            return Response(
                {"detail": "Lỗi hệ thống, không thể tải nội dung xem trước."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )