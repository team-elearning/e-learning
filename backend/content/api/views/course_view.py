import logging
import uuid
from django.http import Http404
from django.core.exceptions import PermissionDenied
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError as DRFValidationError


from content.serializers import CourseSerializer
from content.api.dtos.course_dto import CourseMetadataCreateInput, CourseTemplateCreateInput, CourseMetadataUpdateInput, CourseCatalogPublicOutput, CourseCatalogInstructorOutput, CourseCatalogAdminOutput, CoursePublicOutput, CourseInstructorOutput, CourseAdminOutput 
from content.types import CourseFetchStrategy, CourseFilter
from content.services import course_service
from content.models import Course
from core.exceptions import DomainError, CourseNotFoundError
from core.api.permissions import IsInstructor, IsCourseOwner
from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin



logger = logging.getLogger(__name__)

# ==========================================
# PUBLIC INTERFACE (PUBLIC)
# ==========================================


        


# # ==========================================
# # PUBLIC INTERFACE (ADMIN)
# # ==========================================
# class AdminCourseListCreateView(RoleBasedOutputMixin, APIView):
#     """
#     GET /admin/courses/ - List các course.
#     POST /admin/courses/ - Tạo course mới.
#     """
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser] 

#     output_dto_public = CoursePublicOutput
#     output_dto_admin  = CourseAdminOutput

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.course_service = course_service

#     def get(self, request, *args, **kwargs):
#         """ Lấy list course CỦA TÔI """
#         try:
#             courses_list = self.course_service.get_courses(
#                 filters=CourseFilter(),
#                 strategy=CourseFetchStrategy.ADMIN_LIST
#             )
#             return Response({"instance": courses_list}, status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.error(f"Lỗi trong InstructorCourseListCreateView (GET): {e}", exc_info=True)
#             return Response({"detail": f"Đã xảy ra lỗi: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#     def post(self, request, *args, **kwargs):
#         """ Tạo course mới (logic y hệt Admin post) """
        
#         serializer = CourseSerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
#         except DRFValidationError:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             course_create_dto = CourseCreateInput(**validated_data)
#         except PydanticValidationError as e:
#             return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Gọi hàm create_course chung, vì owner đã được truyền vào
#             new_course = self.course_service.create_course(
#                 data=course_create_dto.model_dump(),
#                 created_by=request.user,
#                 output_strategy=CourseFetchStrategy.ADMIN_DETAIL
#             )
#             return Response({"instance": new_course}, status=status.HTTP_201_CREATED)
#         except DomainError as e: 
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except ValueError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi trong InstructorCourseListCreateView (POST): {e}", exc_info=True)
#             return Response({"detail": f"Lỗi máy chủ khi tạo course - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class AdminCourseDetailView(RoleBasedOutputMixin, CoursePermissionMixin, APIView):
#     """
#     GET /admin/courses/<pk>/    - Lấy chi tiết (của tôi).
#     PATCH /admin/courses/<pk>/  - Cập nhật (của tôi).
#     DELETE /admin/courses/<pk>/ - Xoá (của tôi).
#     """
#     # Phải là Instructor 
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser] 

#     output_dto_public = CoursePublicOutput
#     output_dto_admin  = CourseAdminOutput

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.course_service = course_service

#     def get(self, request, pk: uuid.UUID, *args, **kwargs):
#         """ Lấy chi tiết (Đã tối ưu) """
#         try:
#             # 1. Gọi thẳng service
#             #    Hàm này đã bao gồm cả check quyền owner
#             course = self.course_service.get_course_single(
#                 filters=CourseFilter(course_id=pk),
#                 strategy=CourseFetchStrategy.ADMIN_DETAIL
#             )
            
#             # 2. Trả về
#             return Response({"instance": course}, status=status.HTTP_200_OK)
        
#         except DomainError as e: 
#             # Bắt lỗi từ service (Không tìm thấy hoặc không có quyền)
#             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
#         except Exception as e:
#             logger.error(f"Lỗi không xác định trong DetailView (GET): {e}", exc_info=True)
#             return Response({"detail": f"Lỗi không xác định: {str(e)}"},
#                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#     def patch(self, request, pk: uuid.UUID, *args, **kwargs):
#         """
#         Cập nhật (PATCH) một course theo logic Moodle (granular).
#         View chỉ validate input và ủy quyền cho service.
#         """
        
#         # 1. Validate Input
#         serializer = CourseSerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
#         except DRFValidationError:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         # 2. Convert sang Pydantic DTO (Giống hệt POST)
#         try:
#             # Giả sử CourseUpdateInput có các trường Optional
#             update_dto = CourseUpdateInput(**validated_data)
            
#             # --- ĐIỂM MẤU CHỐT CỦA PATCH ---
#             # Dùng 'exclude_unset=True' để dict chỉ chứa
#             # CÁC TRƯỜNG MÀ USER THỰC SỰ GỬI LÊN.
#             # Service 'patch_course' của chúng ta dựa vào việc key
#             # không tồn tại (ví dụ: 'modules') để biết là "không thay đổi".
#             patch_data = update_dto.model_dump(exclude_unset=True)
            
#         except PydanticValidationError as e:
#             return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#         # 3. "No Updates" Check (Optional, nhưng nên có)
#         # Nếu user gửi body rỗng, hoặc không có trường nào hợp lệ
#         if not patch_data:
#             # Nếu không có gì để cập nhật, chúng ta chỉ cần
#             # lấy và trả về instance hiện tại.
#             try:
#                 instance = self.course_service.get_course_single(
#                     filters=CourseFilter(course_id=pk),
#                     strategy=CourseFetchStrategy.ADMIN_DETAIL # Map sang Admin DTO
#                 )

#                 return Response({"instance": instance}, status=status.HTTP_200_OK)
#             except (DomainError, ValueError) as e:
#                 # (Hoặc Http404 tùy bạn định nghĩa)
#                 return Response({"detail": f"Không tìm thấy course: {e}"}, status=status.HTTP_404_NOT_FOUND)

#         # 4. Gọi Service (Giống hệt POST)
#         # GỌI HÀM 'patch_course' MÀ CHÚNG TA VỪA TẠO
#         try:
#             updated_course = self.course_service.patch_course(
#                 course_id=pk,
#                 data=patch_data, # Dùng dict đã lọc
#                 actor=request.user,
#                 output_strategy=CourseFetchStrategy.ADMIN_DETAIL
#             )
#             # 'updated_course' là một CourseDomain đã được cập nhật
#             return Response({"instance": updated_course}, status=status.HTTP_200_OK)
        
#         # 5. Error Handling (Copy từ POST cho nhất quán)
#         except DomainError as e: 
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except ValueError as e: # service 'patch_course' ném ValueError
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi trong InstructorCourseDetailView (PATCH): {e}", exc_info=True)
#             return Response({"detail": f"Lỗi máy chủ khi cập nhật course - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def delete(self, request, pk: uuid.UUID, *args, **kwargs):
#         """ Xóa """
#         try:
#             # Kiểm tra quyền
#             self.check_course_permission(request, course_id=pk)
#         except Http404 as e:
#             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except PermissionDenied as e:
#             return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        
#         try:
#             self.course_service.delete_course(course_id=pk, actor=request.user)
#             return Response(
#                 {"detail": f"Đã xóa thành công khóa học (ID: {pk})."}, 
#                 status=status.HTTP_200_OK
#             )
#         except DomainError as e: 
#             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        

# class AdminCoursePublishView(RoleBasedOutputMixin, APIView):
#     permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

#     output_dto_public = CoursePublicOutput
#     output_dto_admin  = CourseAdminOutput

#     def post(self, request, pk):
#         """
#         POST /admin/courses/<pk>/publish/
#         Admin có quyền publish bất cứ khóa nào.
#         """
        
#         try:
#             course = course_service.publish_course(
#                 course_id=pk, 
#                 actor=request.user, 
#                 publish_action=True
#             )
#             # Admin thì trả về AdminOutput
#             return Response({"instance": course}, status=status.HTTP_200_OK)
            
#         except ValueError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# class AdminCourseUnpublishView(RoleBasedOutputMixin, APIView):
#     permission_classes = [permissions.IsAdminUser, permissions.IsAuthenticated]

#     output_dto_public = CoursePublicOutput
#     output_dto_admin  = CourseAdminOutput

#     def post(self, request, pk):
#         """
#         POST /admin/courses/<pk>/publish/
#         Admin có quyền publish bất cứ khóa nào.
#         """
        
#         try:
#             course = course_service.publish_course(
#                 course_id=pk, 
#                 actor=request.user, 
#                 publish_action=False
#             )
#             # Admin thì trả về AdminOutput
#             return Response({"instance": course}, status=status.HTTP_200_OK)
            
#         except ValueError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# PUBLIC INTERFACE (INSTRUCTOR)
# ==========================================
class InstructorCourseListCreateView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /instructor/courses/ - List các course CỦA TÔI.
    POST /instructor/courses/ - Tạo course meatdata (owner là TÔI).
    """
    permission_classes = [IsInstructor] # Chỉ Instructor mới được vào

    permission_lookup = {'course_id': Course}

    # Instructor cũng thấy DTO admin cho course của mình
    output_dto_public = CourseCatalogPublicOutput
    output_dto_instructor = CourseCatalogInstructorOutput
    output_dto_admin  = CourseCatalogAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, *args, **kwargs):
        """ Lấy list course CỦA TÔI """
        try:
            courses_list = self.course_service.get_courses(
                filters=CourseFilter(owner=request.user), # Tự động check quyền owner
                strategy=CourseFetchStrategy.INSTRUCTOR_DASHBOARD
            )
            return Response({"instance": courses_list}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Lỗi trong InstructorCourseListCreateView (GET): {e}", exc_info=True)
            return Response({"detail": f"Đã xảy ra lỗi: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request, *args, **kwargs):
        """ Tạo course mới (logic y hệt Admin post) """
        
        serializer = CourseSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            course_create_dto = CourseMetadataCreateInput(**validated_data)
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Gọi hàm create_course chung, vì owner đã được truyền vào
            new_course = self.course_service.create_course_metadata(
                data=course_create_dto.model_dump(),
                created_by=request.user,
                output_strategy=CourseFetchStrategy.BASIC
            )
            return Response({"instance": new_course}, status=status.HTTP_201_CREATED)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong InstructorCourseListCreateView (POST): {e}", exc_info=True)
            return Response({"detail": f"Lỗi máy chủ khi tạo course - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstructorCourseDetailView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /instructor/courses/<pk>/    - Lấy chi tiết (của tôi).
    PATCH /instructor/courses/<pk>/  - Cập nhật (của tôi).
    DELETE /instructor/courses/<pk>/ - Xoá (của tôi).
    """
    # Phải là Instructor 
    permission_classes = [permissions.IsAuthenticated, IsInstructor, IsCourseOwner] 

    permission_lookup = {'course_id': Course}

    output_dto_public = CoursePublicOutput
    output_dto_instructor = CourseInstructorOutput
    output_dto_admin  = CourseAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Lấy chi tiết (Đã tối ưu) """
        try:
            # 1. Gọi thẳng service
            #    Hàm này đã bao gồm cả check quyền owner
            course = self.course_service.get_course_single(
                filters=CourseFilter(course_id=pk, owner=request.user), # Tự động check quyền owner
                strategy=CourseFetchStrategy.INSTRUCTOR_DETAIL
            )
            # 2. Trả về
            return Response({"instance": course}, status=status.HTTP_200_OK)
        
        except DomainError as e: 
            # Bắt lỗi từ service (Không tìm thấy hoặc không có quyền)
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Lỗi không xác định trong DetailView (GET): {e}", exc_info=True)
            return Response({"detail": f"Lỗi không xác định: {str(e)}"},
                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        Cập nhật (PATCH) một course theo logic Moodle (granular).
        View chỉ validate input và ủy quyền cho service.
        """
        
        # 1. Validate Input 
        serializer = CourseSerializer(data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Convert sang Pydantic DTO (Giống hệt POST)
        try:
            # Giả sử CourseUpdateInput có các trường Optional
            update_dto = CourseMetadataUpdateInput(**validated_data)
                        
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated_course = self.course_service.update_course_metadata(
                course_id=pk,
                data=update_dto.to_dict(), # Dùng dict đã lọc
                updated_by=request.user,
                output_strategy=CourseFetchStrategy.STRUCTURE
            )
            # 'updated_course' là một CourseDomain đã được cập nhật
            return Response({"instance": updated_course}, status=status.HTTP_200_OK)
        
        # 5. Error Handling (Copy từ POST cho nhất quán)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e: # service 'patch_course' ném ValueError
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong InstructorCourseDetailView (PATCH): {e}", exc_info=True)
            return Response({"detail": f"Lỗi máy chủ khi cập nhật course - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Xóa """

        try:
            self.course_service.delete_course(course_id=pk, actor=request.user)
            return Response(
                {"detail": f"Đã xóa thành công khóa học (ID: {pk})."}, 
                status=status.HTTP_200_OK
            )
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        

# class InstructorCoursePublishView(RoleBasedOutputMixin, APIView):
#     permission_classes = [permissions.IsAuthenticated, IsInstructor]

#     output_dto_public = CoursePublicOutput
#     output_dto_admin  = CourseAdminOutput

#     def post(self, request, pk):
#         """
#         POST /instructor/courses/<pk>/publish/
#         """

#         try:
#             course = course_service.publish_course(
#                 course_id=pk, 
#                 actor=request.user, 
#                 publish_action=True
#             )

#             return Response({"instance": course}, status=status.HTTP_200_OK)
            
#         except ValueError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# class InstructorCourseUnpublishView(RoleBasedOutputMixin, APIView):
#     permission_classes = [permissions.IsAuthenticated, IsInstructor]

#     output_dto_public = CoursePublicOutput
#     output_dto_admin  = CourseAdminOutput

#     def post(self, request, pk):
#         """
#         POST /instructor/courses/<pk>/publish/
#         """

#         try:
#             course = course_service.publish_course(
#                 course_id=pk, 
#                 actor=request.user, 
#                 publish_action=False
#             )

#             return Response({"instance": course}, status=status.HTTP_200_OK)
            
#         except ValueError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InstructorCourseTemplateCreateView(RoleBasedOutputMixin, APIView):
    """
    POST /instructor/courses/template/ - Tạo course template mới (owner là TÔI).
    """
    permission_classes = [IsInstructor] # Chỉ Instructor mới được vào

    # Instructor cũng thấy DTO admin cho course của mình
    output_dto_public = CoursePublicOutput
    output_dto_admin  = CourseAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service
        
    def post(self, request, *args, **kwargs):
        """ Tạo course mới (logic y hệt Admin post) """
        
        serializer = CourseSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            course_create_dto = CourseTemplateCreateInput(**validated_data)
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Gọi hàm create_course chung, vì owner đã được truyền vào
            new_course = self.course_service.create_course_from_template(
                data=course_create_dto.model_dump(),
                created_by=request.user,
                output_strategy=CourseFetchStrategy.STRUCTURE
            )
            return Response({"instance": new_course}, status=status.HTTP_201_CREATED)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong InstructorCourseListCreateView (POST): {e}", exc_info=True)
            return Response({"detail": f"Lỗi máy chủ khi tạo course - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
