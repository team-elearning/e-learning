import logging
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError as DRFValidationError
  
from core.exceptions import DomainError, CourseNotFoundError
from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin
from core.api.permissions import CanViewCourseContent
from content.api.dtos.course_dto import CourseCatalogPublicOutput, MyCourseCatalogOutput, CourseCatalogAdminOutput, CoursePublicOutput, CourseAdminOutput
from content.api.dtos.content_block_dto import ContentBlockPublicOutput, ContentBlockAdminOutput
from content.api.dtos.enrollment_dto import EnrollmentInput, EnrollmentOutput, EnrollmentListOutput
from content.types import CourseFetchStrategy, CourseFilter
from content.services import enrollment_service, course_service, content_block_service
from content.serializers import EnrollmentCreateSerializer
from content.models import Course, ContentBlock



logger = logging.getLogger(__name__)

# ==========================================
# PUBLIC INTERFACE (PUBLIC)
# ==========================================

class CourseEnrollView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    POST /courses/<pk>/enroll/ -> Ghi danh user hiện tại vào khóa học.
    DELETE /courses/<pk>/unenroll/ -> Hủy ghi danh user hiện tại.
    """
    permission_classes = [permissions.IsAuthenticated]

    permission_lookup = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Giữ sự nhất quán với các View khác của bạn
        self.enrollment_service = enrollment_service 

    def post(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        Ghi danh user hiện tại (request.user) vào khóa học (pk).
        """
        try:
            # 1. Ủy quyền hoàn toàn cho service
            # Service sẽ lo việc:
            # - Tìm course (published=True)
            # - Check xem user có phải owner không
            # - Check xem user đã enroll chưa
            # - Tạo record Enrollment
            
            # (Chúng ta sẽ định nghĩa hàm này ở bước 2)
            enrollment_domain = self.enrollment_service.enroll_user_in_course(
                course_id=pk, 
                user=request.user
            )
            
            # 2. Trả về thành công
            # POST tạo mới resource nên dùng 201 CREATED
            return Response(
                {"detail": "Ghi danh thành công."},
                status=status.HTTP_201_CREATED 
            )
        
        except DomainError as e:
            # Lỗi nghiệp vụ (đã enroll, là owner, course not found)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # Lỗi hệ thống
            logger.error(f"Lỗi trong CourseEnrollView (POST): {e}", exc_info=True)
            return Response({"detail": f"Lỗi máy chủ khi ghi danh - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        Hủy ghi danh user hiện tại (request.user) khỏi khóa học (pk).
        """
        try:
            # 1. Ủy quyền hoàn toàn cho service
            # Service sẽ lo việc:
            # - Tìm record Enrollment
            # - Xóa record
            
            # (Chúng ta sẽ định nghĩa hàm này ở bước 2)
            self.enrollment_service.unenroll_user_from_course(
                course_id=pk, 
                user=request.user
            )
            
            # 2. Trả về thành công
            return Response(
                {"detail": "Hủy ghi danh thành công."},
                status=status.HTTP_200_OK # DELETE thành công
            )
        
        except DomainError as e:
            # Lỗi nghiệp vụ (chưa enroll, course not found)
            # Dùng 404 vì không tìm thấy record enrollment
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND) 
        
        except Exception as e:
            # Lỗi hệ thống
            logger.error(f"Lỗi trong CourseEnrollView (DELETE): {e}", exc_info=True)
            return Response({"detail": f"Lỗi máy chủ khi hủy ghi danh - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PublicCourseListView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /courses/ - List các courses public (Trừ những khóa user đã học).
    """
    # IsAuthenticated: Phải đăng nhập
    # IsAllowAny: Ai cũng thấy (thay thế nếu cần)
    permission_classes = [permissions.IsAuthenticated] 

    permission_lookup = {}

    # Cấu hình DTO output
    output_dto_public = CoursePublicOutput
    output_dto_admin  = CourseAdminOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, *args, **kwargs):
        """
        Xử lý GET request để list courses chưa ghi danh.
        """
        try:
            courses_list = self.course_service.get_courses(
                filters=CourseFilter(
                    published_only=True,
                    exclude_enrolled_user=request.user),
                strategy=CourseFetchStrategy.CATALOG_LIST
            )
            return Response({"instance": courses_list}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Lỗi trong PublicCourseListView (GET): {e}", exc_info=True)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MyEnrolledCourseListView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /my-courses/ - List các khóa học MÀ TÔI ĐÃ GHI DANH.
    """
    # 1. Bắt buộc phải đăng nhập
    permission_classes = [permissions.IsAuthenticated] 
    permission_lookup = {}

    # 2. Dùng chung DTO với public list (hoặc một DTO khác nếu muốn)
    #    User xem các khóa học của mình cũng chỉ cần thông tin public.
    output_dto_public = MyCourseCatalogOutput
    output_dto_admin  = MyCourseCatalogOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, *args, **kwargs):
        """
        Lấy danh sách các khóa học user hiện tại đã ghi danh.
        """
        try:
            # 3. Gọi hàm service MỚI, chuyên biệt
            enrolled_courses_list = self.course_service.get_courses(
                filters=CourseFilter(enrolled_user=request.user), # Tự động distinct() bên trong
                strategy=CourseFetchStrategy.MY_ENROLLED
            )
            
            # 4. Trả về
            return Response({"instance": enrolled_courses_list}, status=status.HTTP_200_OK)
        
        except Exception as e:
            # (Xử lý lỗi chuẩn)
            logger.error(f"Lỗi trong MyEnrolledCourseListView (GET): {e}", exc_info=True)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class CourseStructureView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /courses/<pk>/ - Lấy chi tiết course (public).
    """
    permission_classes = [permissions.IsAuthenticated]

    permission_lookup = {"course_id": Course}

    # Cấu hình DTO output
    output_dto_public = CoursePublicOutput
    output_dto_admin  = CourseAdminOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, course_id: uuid.UUID, *args, **kwargs):
        """
        Xử lý GET request để lấy chi tiết một course.
        """
        try:
            course = self.course_service.get_course_single(
                filters=CourseFilter(course_id=course_id, enrolled_user=request.user), # Check đã enroll chưa
                strategy=CourseFetchStrategy.STRUCTURE
            )
            return Response({"instance": course}, status=status.HTTP_200_OK)
        
        except DomainError as e: # Lỗi "Not Found"
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        except CourseNotFoundError as e:
            # Trường hợp chưa ghi danh hoặc không có quyền truy cập khóa học
            return Response(
                {"detail": "Bạn chưa ghi danh vào khóa học này."},
                status=status.HTTP_403_FORBIDDEN
            )

        except Exception as e:
            logger.error(f"Lỗi trong PublicCourseDetailView (GET): {e}", exc_info=True)
            return Response({"detail": f"Lỗi máy chủ: {str(e)}"},
                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ContentBlockDetailView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET    /blocks/{block_id}/  - Lấy chi tiết
    """
    permission_classes = [permissions.IsAuthenticated, CanViewCourseContent]
    
    # Permission check: Block -> Lesson -> Module -> Course -> Owner
    permission_lookup = {'block_id': ContentBlock}

    output_dto_public = ContentBlockPublicOutput
    output_dto_admin = ContentBlockAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content_block_service = content_block_service

    def get(self, request, block_id: uuid.UUID, *args, **kwargs):
        """Lấy chi tiết 1 block"""
        try:
            block_detail = self.content_block_service.get_content_block_detail(
                block_id=block_id
            )
            return Response({"instance": block_detail}, status=status.HTTP_200_OK)
            
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": f"Lỗi server - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# # ==========================================
# # PUBLIC INTERFACE (INSTRUCTOR)
# # ==========================================

# class InstructorCourseParticipantListView(RoleBasedOutputMixin, APIView):
#     """
#     GET /courses/<pk>/users/ 
#     -> Lấy danh sách học viên của khóa học (Chỉ Owner mới được xem).
    
#     POST /courses/<pk>/users/
#     -> Giảng viên thêm thủ công 1 user vào khóa học (Manual Enrollment).
#     """
#     permission_classes = [permissions.IsAuthenticated]

#     output_dto_public = EnrollmentListOutput 
#     output_dto_admin  = EnrollmentListOutput

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.enrollment_service = enrollment_service

#     def get(self, request, pk: uuid.UUID, *args, **kwargs):
#         """
#         Lấy danh sách Users đã enroll vào khóa học <pk>.
#         """
#         try:
#             # Service cần check: request.user phải là Owner của course <pk>
#             collection_domain = self.enrollment_service.get_course_participants(
#                 course_id=pk,
#                 actor=request.user 
#             )

#             # Trả về danh sách (có thể bọc trong DTO UserOutput nếu cần)
#             return Response({"instance": collection_domain}, status=status.HTTP_200_OK)

#         except DomainError as e:
#             # Ví dụ: Không phải owner, Course không tồn tại
#             return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
#         except Exception as e:
#             logger.error(f"Lỗi trong CourseParticipantListView (GET): {e}", exc_info=True)
#             return Response({"detail": f"Lỗi máy chủ. : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def post(self, request, pk: uuid.UUID, *args, **kwargs):
#         """
#         Giảng viên thêm thủ công học viên (bằng user_id/email).
#         Body: { "user_id": "..." }
#         """
#         serializer = EnrollmentCreateSerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
#         except DRFValidationError:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         try:            
#             input_dto = EnrollmentInput(**validated_data)

#             # Gọi service: enroll user target_user_id vào course pk, thực hiện bởi request.user
#             self.enrollment_service.manual_enroll_user(
#                 course_id=pk,
#                 input=input_dto.to_dict(),
#                 actor=request.user 
#             )
            
#             return Response({"detail": "Thêm học viên thành công."}, status=status.HTTP_201_CREATED)

#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi trong CourseParticipantListView (POST): {e}", exc_info=True)
#             return Response({"detail": f"Lỗi máy chủ - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class InstructorCourseParticipantDetailView(RoleBasedOutputMixin, APIView):
#     """
#     DELETE /courses/<pk>/users/<user_id>/
#     -> Giảng viên "kick" (xóa) học viên khỏi khóa học.
#     """
#     permission_classes = [permissions.IsAuthenticated]

#     output_dto_public = EnrollmentOutput
#     output_dto_admin  = EnrollmentOutput

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.enrollment_service = enrollment_service

#     def get(self, request, pk: uuid.UUID, user_id: uuid.UUID, *args, **kwargs):
#         """
#         Lấy thông tin chi tiết về việc học của user_id trong course pk.
#         """
#         try:
#             participant_enrollment = self.enrollment_service.get_participant_detail(
#                 course_id=pk,
#                 target_user_id=user_id,
#                 actor=request.user
#             )
            
#             # Lưu ý: 'participant_enrollment' là 1 object Enrollment model.
#             # Serializer của bạn cần xử lý để lấy ra data user (username, email) từ relationship này.
#             return Response({"instance": participant_enrollment}, status=status.HTTP_200_OK)

#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi trong CourseParticipantDetailView (GET): {e}", exc_info=True)
#             return Response({"detail": f"Lỗi máy chủ - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def delete(self, request, pk: uuid.UUID, user_id: uuid.UUID, *args, **kwargs):
#         """
#         Xóa user (user_id) khỏi course (pk).
#         """
#         try:
#             # Service check: request.user là owner, user_id có trong lớp không
#             self.enrollment_service.kick_student_from_course(
#                 course_id=pk,
#                 target_user_id=user_id,
#                 actor=request.user
#             )
            
#             return Response({"detail": "Đã xóa học viên khỏi khóa học."}, status=status.HTTP_200_OK)

#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
#         except Exception as e:
#             logger.error(f"Lỗi trong CourseParticipantDetailView (DELETE): {e}", exc_info=True)
#             return Response({"detail": f"Lỗi máy chủ khi xóa học viên - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# # ==========================================
# # PUBLIC INTERFACE (ADMIN)
# # ==========================================

# class AdminCourseParticipantListView(RoleBasedOutputMixin, APIView):
#     """
#     GET /courses/<pk>/users/ 
#     -> Lấy danh sách học viên của khóa học (Chỉ Owner mới được xem).
    
#     POST /courses/<pk>/users/
#     -> Giảng viên thêm thủ công 1 user vào khóa học (Manual Enrollment).
#     """
#     permission_classes = [permissions.IsAuthenticated]

#     output_dto_public = EnrollmentOutput
#     output_dto_admin  = EnrollmentOutput

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.enrollment_service = enrollment_service

#     def get(self, request, pk: uuid.UUID, *args, **kwargs):
#         """
#         Lấy danh sách Users đã enroll vào khóa học <pk>.
#         """
#         try:
#             # Service cần check: request.user phải là Owner của course <pk>
#             participants = self.enrollment_service.get_course_participants(
#                 course_id=pk,
#                 actor=request.user 
#             )
            
#             # Trả về danh sách (có thể bọc trong DTO UserOutput nếu cần)
#             return Response({"instance": participants}, status=status.HTTP_200_OK)

#         except DomainError as e:
#             # Ví dụ: Không phải owner, Course không tồn tại
#             return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
#         except Exception as e:
#             logger.error(f"Lỗi trong CourseParticipantListView (GET): {e}", exc_info=True)
#             return Response({"detail": f"Lỗi máy chủ. : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def post(self, request, pk: uuid.UUID, *args, **kwargs):
#         """
#         Giảng viên thêm thủ công học viên (bằng user_id/email).
#         Body: { "user_id": "..." }
#         """
#         try:
#             target_user_id = request.data.get('user_id')
#             if not target_user_id:
#                 return Response({"detail": "Thiếu user_id"}, status=status.HTTP_400_BAD_REQUEST)

#             # Gọi service: enroll user target_user_id vào course pk, thực hiện bởi request.user
#             self.enrollment_service.manual_enroll_user(
#                 course_id=pk,
#                 target_user_id=target_user_id,
#                 actor=request.user 
#             )
            
#             return Response({"detail": "Thêm học viên thành công."}, status=status.HTTP_201_CREATED)

#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi trong CourseParticipantListView (POST): {e}", exc_info=True)
#             return Response({"detail": f"Lỗi máy chủ - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class AdminCourseParticipantDetailView(RoleBasedOutputMixin, APIView):
#     """
#     DELETE /courses/<pk>/users/<user_id>/
#     -> Giảng viên "kick" (xóa) học viên khỏi khóa học.
#     """
#     permission_classes = [permissions.IsAuthenticated]

#     output_dto_public = EnrollmentOutput
#     output_dto_admin  = EnrollmentOutput

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.enrollment_service = enrollment_service

#     def get(self, request, pk: uuid.UUID, user_id: uuid.UUID, *args, **kwargs):
#         """
#         Lấy thông tin chi tiết về việc học của user_id trong course pk.
#         """
#         try:
#             participant_enrollment = self.enrollment_service.get_participant_detail(
#                 course_id=pk,
#                 target_user_id=user_id,
#                 actor=request.user
#             )
            
#             # Lưu ý: 'participant_enrollment' là 1 object Enrollment model.
#             # Serializer của bạn cần xử lý để lấy ra data user (username, email) từ relationship này.
#             return Response({"instance": participant_enrollment}, status=status.HTTP_200_OK)

#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi trong CourseParticipantDetailView (GET): {e}", exc_info=True)
#             return Response({"detail": f"Lỗi máy chủ - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def delete(self, request, pk: uuid.UUID, user_id: uuid.UUID, *args, **kwargs):
#         """
#         Xóa user (user_id) khỏi course (pk).
#         """
#         try:
#             # Service check: request.user là owner, user_id có trong lớp không
#             self.enrollment_service.kick_student_from_course(
#                 course_id=pk,
#                 target_user_id=user_id,
#                 actor=request.user
#             )
            
#             return Response({"detail": "Đã xóa học viên khỏi khóa học."}, status=status.HTTP_200_OK)

#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
#         except Exception as e:
#             logger.error(f"Lỗi trong CourseParticipantDetailView (DELETE): {e}", exc_info=True)
#             return Response({"detail": f"Lỗi máy chủ khi xóa học viên - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)