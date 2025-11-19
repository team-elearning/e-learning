import logging
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from pydantic import ValidationError as PydanticValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.http import Http404

from content.serializers import CourseCreateSerializer, CoursePatchInputSerializer
from content.services import course_service     
from content.api.dtos.course_dto import CoursePublicOutput, CourseAdminOutput, CourseCreateInput, CourseUpdateInput
from core.exceptions import DomainError, CourseNotFoundError
from core.api.permissions import IsInstructor
from core.api.mixins import RoleBasedOutputMixin, CoursePermissionMixin



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
    output_dto_admin  = CourseAdminOutput 

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
        

class MyEnrolledCourseListView(RoleBasedOutputMixin, APIView):
    """
    GET /my-courses/ - List các khóa học MÀ TÔI ĐÃ GHI DANH.
    """
    # 1. Bắt buộc phải đăng nhập
    permission_classes = [permissions.IsAuthenticated] 

    # 2. Dùng chung DTO với public list (hoặc một DTO khác nếu muốn)
    #    User xem các khóa học của mình cũng chỉ cần thông tin public.
    output_dto_public = CoursePublicOutput
    output_dto_admin  = CourseAdminOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, *args, **kwargs):
        """
        Lấy danh sách các khóa học user hiện tại đã ghi danh.
        """
        try:
            # 3. Gọi hàm service MỚI, chuyên biệt
            enrolled_courses_list = self.course_service.list_enrolled_courses_for_user(
                user=request.user
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


class PublicCourseDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /courses/<pk>/ - Lấy chi tiết course (public).
    """
    permission_classes = [permissions.IsAuthenticated]

    # Cấu hình DTO output
    output_dto_public = CoursePublicOutput
    output_dto_admin  = CoursePublicOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        Xử lý GET request để lấy chi tiết một course.
        """
        try:
            course = self.course_service.get_enrolled_course_detail_for_user(
                course_id=pk,
                user=request.user,
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
            return Response({"detail": f"Lỗi máy chủ: {e}"},
                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CourseEnrollView(APIView):
    """
    POST /courses/<pk>/enroll/ -> Ghi danh user hiện tại vào khóa học.
    DELETE /courses/<pk>/unenroll/ -> Hủy ghi danh user hiện tại.
    """
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Giữ sự nhất quán với các View khác của bạn
        self.course_service = course_service 

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
            enrollment_domain = self.course_service.enroll_user_in_course(
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
            return Response({"detail": "Lỗi máy chủ khi ghi danh."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            self.course_service.unenroll_user_from_course(
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
            return Response({"detail": "Lỗi máy chủ khi hủy ghi danh."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ------------------ ADMIN -------------------------------
class AdminCourseListCreateView(RoleBasedOutputMixin, APIView):
    """
    GET /admin/courses/ - List các course.
    POST /admin/courses/ - Tạo course mới.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser] 

    output_dto_public = CoursePublicOutput
    output_dto_admin  = CourseAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, *args, **kwargs):
        """ Lấy list course CỦA TÔI """
        try:
            courses_list = self.course_service.list_all_course_overviews()
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
            new_course = self.course_service.create_course_admin(
                data=course_create_dto.model_dump(),
                owner=request.user
            )
            return Response({"instance": new_course}, status=status.HTTP_201_CREATED)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong InstructorCourseListCreateView (POST): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi tạo course."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminCourseDetailView(RoleBasedOutputMixin, CoursePermissionMixin, APIView):
    """
    GET /admin/courses/<pk>/    - Lấy chi tiết (của tôi).
    PATCH /admin/courses/<pk>/  - Cập nhật (của tôi).
    DELETE /admin/courses/<pk>/ - Xoá (của tôi).
    """
    # Phải là Instructor 
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser] 

    output_dto_public = CoursePublicOutput
    output_dto_admin  = CourseAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Lấy chi tiết (Đã tối ưu) """
        try:
            # 1. Gọi thẳng service
            #    Hàm này đã bao gồm cả check quyền owner
            course = self.course_service.get_course_detail_admin(course_id=pk)
            
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
        
        # 1. Validate Input (Giống hệt POST)
        # KHÔNG cần lấy instance hay check permission ở đây.
        # Service 'patch_course' sẽ làm việc đó.
        
        # GHI CHÚ: Bạn cần một Serializer (ví dụ: CoursePatchInputSerializer)
        # chỉ để validate input, KHÔNG phải là ModelSerializer cần 'instance'.
        # Nó giống hệt 'CourseCreateSerializer' của bạn.
        serializer = CoursePatchInputSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Convert sang Pydantic DTO (Giống hệt POST)
        try:
            # Giả sử CourseUpdateInput có các trường Optional
            update_dto = CourseUpdateInput(**validated_data)
            
            # --- ĐIỂM MẤU CHỐT CỦA PATCH ---
            # Dùng 'exclude_unset=True' để dict chỉ chứa
            # CÁC TRƯỜNG MÀ USER THỰC SỰ GỬI LÊN.
            # Service 'patch_course' của chúng ta dựa vào việc key
            # không tồn tại (ví dụ: 'modules') để biết là "không thay đổi".
            patch_data = update_dto.model_dump(exclude_unset=True)
            
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. "No Updates" Check (Optional, nhưng nên có)
        # Nếu user gửi body rỗng, hoặc không có trường nào hợp lệ
        if not patch_data:
            # Nếu không có gì để cập nhật, chúng ta chỉ cần
            # lấy và trả về instance hiện tại.
            try:
                instance = self.course_service.get_course_detail_admin(course_id=pk)

                return Response({"instance": instance}, status=status.HTTP_200_OK)
            except (DomainError, ValueError) as e:
                # (Hoặc Http404 tùy bạn định nghĩa)
                return Response({"detail": f"Không tìm thấy course: {e}"}, status=status.HTTP_404_NOT_FOUND)

        # 4. Gọi Service (Giống hệt POST)
        # GỌI HÀM 'patch_course' MÀ CHÚNG TA VỪA TẠO
        try:
            updated_course = self.course_service.patch_course_admin(
                course_id=pk,
                data=patch_data, # Dùng dict đã lọc
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
            return Response({"detail": "Lỗi máy chủ khi cập nhật course."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            self.course_service.delete_course_by_id(course_id=pk)
            return Response(
                {"detail": f"Đã xóa thành công khóa học (ID: {pk})."}, 
                status=status.HTTP_200_OK
            )
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        

# class AdminCoursePublishView(RoleBasedOutputMixin, APIView):
#     """
#     POST /courses/{id}/publish/
#     body: {"require_all_lessons_published": false}
#     """
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

#     def post(self, request, course_id: str):
#         require_all = request.data.get("require_all_lessons_published", False)
#         course_domain = course_service.get_course(course_id)
#         if not course_domain:
#             return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
#         try:
#             # Using a simple dict as command for simplicity, matching service layer
#             publish_command_data = {"published": True, "require_all_lessons_published": require_all}
#             course_domain = course_service.publish_course(course_id=course_id, publish_data=type("PublishCmd", (), publish_command_data))
            
#             return Response(course_domain)
#         except Exception as exc:
#             return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# class AdminCourseUnpublishView(RoleBasedOutputMixin, APIView):
#     """
#     POST /courses/{id}/unpublish/
#     """
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

#     def post(self, request, course_id: str):
#         try:
#             updated = course_service.unpublish_course(course_id=course_id)
#             if not updated:
#                 return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
            
#             return Response(updated)
#         except Exception as ex:
#             return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


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
            courses_list = self.course_service.list_course_overviews_instructor(owner=request.user)
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
            new_course = self.course_service.create_course_instructor(
                data=course_create_dto.model_dump(),
                owner=request.user
            )
            return Response({"instance": new_course}, status=status.HTTP_201_CREATED)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
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
    permission_classes = [permissions.IsAuthenticated, IsInstructor] 

    output_dto_public = CoursePublicOutput
    output_dto_admin  = CourseAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_service = course_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Lấy chi tiết (Đã tối ưu) """
        try:
            # 1. Gọi thẳng service
            #    Hàm này đã bao gồm cả check quyền owner
            course = self.course_service.get_course_instructor(
                course_id=pk, 
                owner=request.user
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
        
        # 1. Validate Input (Giống hệt POST)
        # KHÔNG cần lấy instance hay check permission ở đây.
        # Service 'patch_course' sẽ làm việc đó.
        
        # GHI CHÚ: Bạn cần một Serializer (ví dụ: CoursePatchInputSerializer)
        # chỉ để validate input, KHÔNG phải là ModelSerializer cần 'instance'.
        # Nó giống hệt 'CourseCreateSerializer' của bạn.
        serializer = CoursePatchInputSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Convert sang Pydantic DTO (Giống hệt POST)
        try:
            # Giả sử CourseUpdateInput có các trường Optional
            update_dto = CourseUpdateInput(**validated_data)
            
            # --- ĐIỂM MẤU CHỐT CỦA PATCH ---
            # Dùng 'exclude_unset=True' để dict chỉ chứa
            # CÁC TRƯỜNG MÀ USER THỰC SỰ GỬI LÊN.
            # Service 'patch_course' của chúng ta dựa vào việc key
            # không tồn tại (ví dụ: 'modules') để biết là "không thay đổi".
            patch_data = update_dto.model_dump(exclude_unset=True)
            
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. "No Updates" Check (Optional, nhưng nên có)
        # Nếu user gửi body rỗng, hoặc không có trường nào hợp lệ
        if not patch_data:
            # Nếu không có gì để cập nhật, chúng ta chỉ cần
            # lấy và trả về instance hiện tại.
            try:
                instance = self.course_service.get_course_instructor(
                    course_id=pk, owner=request.user
                )
                return Response({"instance": instance}, status=status.HTTP_200_OK)
            except (DomainError, ValueError) as e:
                # (Hoặc Http404 tùy bạn định nghĩa)
                return Response({"detail": f"Không tìm thấy course: {e}"}, status=status.HTTP_404_NOT_FOUND)

        # 4. Gọi Service (Giống hệt POST)
        # GỌI HÀM 'patch_course' MÀ CHÚNG TA VỪA TẠO
        try:
            updated_course = self.course_service.patch_course_instructor(
                course_id=pk,
                data=patch_data, # Dùng dict đã lọc
                owner=request.user
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
            return Response({"detail": "Lỗi máy chủ khi cập nhật course."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            self.course_service.delete_course_for_instructor(course_id=pk, owner=request.user)
            return Response(
                {"detail": f"Đã xóa thành công khóa học (ID: {pk})."}, 
                status=status.HTTP_200_OK
            )
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        

# class InstructorCoursePublishView(APIView):
#     """
#     POST /instructor/courses/{id}/publish/
#     """
#     permission_classes = [IsInstructor] 

#     def post(self, request, course_id: str):
#         try:
#             # Kiểm tra quyền
#             self.check_course_permission(request, course_id=course_id)
#         except Http404 as e:
#             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except PermissionDenied as e:
#             return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        
#         require_all = request.data.get("require_all_lessons_published", False)
        
#         try:
#             publish_command_data = {"published": True, "require_all_lessons_published": require_all}
            
#             # Gọi service mới của Instructor
#             course_domain = course_service.publish_course_for_instructor(
#                 course_id=course_id, 
#                 publish_data=type("PublishCmd", (), publish_command_data),
#                 owner=request.user
#             )
            
#             # Trả về DTO (thay vì Serializer)
#             return Response(course_domain, status=status.HTTP_200_OK)

#         except (DomainError, InvalidOperation) as exc:
#             return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as exc:
#             return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# class InstructorCourseUnpublishView(APIView):
#     """
#     POST /api/v1/instructor/courses/{id}/unpublish/
#     """
#     permission_classes = [IsInstructor]

#     def post(self, request, course_id: str):
#         try:
#             # Kiểm tra quyền
#             self.check_course_permission(request, course_id=course_id)
#         except Http404 as e:
#             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except PermissionDenied as e:
#             return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        
#         try:
#             # Gọi service mới của Instructor
#             course_domain = course_service.unpublish_course_for_instructor(
#                 course_id=course_id,
#                 owner=request.user
#             )
            
#             if not course_domain:
#                  return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

#             return Response(CourseAdminOutput.model_validate(course_domain).model_dump(), status=status.HTTP_200_OK)
            
#         except (DomainError, InvalidOperation) as ex:
#             return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as ex:
#             return Response({"detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)
