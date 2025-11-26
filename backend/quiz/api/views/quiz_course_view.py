import logging
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError as DRFValidationError
from pydantic import ValidationError as PydanticValidationError

from core.exceptions import DomainError
from quiz.serializers import QuizCourseSerializer
from quiz.api.dtos.quiz_course_dto import QuizUpdateInput, QuizInstructorOutput, QuizAdminOutput, QuizPublicOutput
from quiz.services import quiz_course_service
from core.api.permissions import IsInstructor
from core.api.mixins import RoleBasedOutputMixin 

logger = logging.getLogger(__name__)

# ======================================================================
# 1. VIEW (USER)
# ======================================================================

class QuizCourseAttemptView(RoleBasedOutputMixin, APIView):
    """
    GET quizzes/<quiz_id>/
    Chức năng: Lấy nội dung bài Quiz để hiển thị lên màn hình.
    """
    permission_classes = [permissions.IsAuthenticated] # Học viên chỉ cần login

    output_dto_admin = QuizAdminOutput
    output_dto_public = QuizPublicOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = quiz_course_service

    def get(self, request, quiz_id: uuid.UUID, *args, **kwargs):
        """ Xem màn hình chờ (Info) """
        try:
            # 1. Gọi Service lấy Domain Data
            quiz_domain = self.service.get_quiz_content(
                quiz_id=quiz_id, 
                user=request.user
            )
            return Response({"instance": quiz_domain}, status=status.HTTP_200_OK)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Lỗi hệ thống - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ======================================================================
# 1. VIEW (Admin)
# ======================================================================

class AdminQuizListView(RoleBasedOutputMixin, APIView):
    """
    GET /api/quizzes/ - List toàn bộ Quiz (Chỉ Admin).
    (Không có POST vì Quiz được tạo lồng trong Course)
    """
    permission_classes = [permissions.IsAdminUser]

    # (Giả sử) DTO cho Output
    output_dto_admin = QuizAdminOutput
    output_dto_public = QuizPublicOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tiêm (inject) service
        self.quiz_service = quiz_course_service

    def get(self, request, *args, **kwargs):
        """ Lấy list toàn bộ quiz """
        try:
            # Service trả về một list các QuizDomain (hoặc DTO)
            quizzes_list = self.quiz_service.list_all_quizzes()
            
            # Mixin (RoleBasedOutputMixin) sẽ tự xử lý "instance"
            return Response({"instance": quizzes_list}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Lỗi trong QuizListAdminView (GET): {e}", exc_info=True)
            return Response({"detail": f"Đã xảy ra lỗi: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminQuizDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /admin/quizzes/<pk>/    - Lấy chi tiết 1 Quiz (cùng câu hỏi).
    PATCH /admin/quizzes/<pk>/  - Cập nhật 1 Quiz (logic C/U/D lồng).
    DELETE /admin/quizzes/<pk>/ - Xóa 1 Quiz.
    """
    # (Giả sử) Cần là Instructor (hoặc Admin) và service sẽ
    # kiểm tra quyền sở hữu (owner)
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser] 

    # (Giả sử) DTO cho Output
    output_dto_admin = QuizAdminOutput
    output_dto_public = QuizPublicOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_course_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Click 1 Quiz (Bao gồm cả 'questions') """
        try:
            # Service sẽ kiểm tra quyền (user) và trả về QuizDomain (đã lồng)
            quiz = self.quiz_service.get_quiz_details(
                quiz_id=pk, 
                user=request.user
            )
            return Response({"instance": quiz}, status=status.HTTP_200_OK)
        
        except DomainError as e: 
            # Bắt lỗi "Không tìm thấy" hoặc "Không có quyền" từ service
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Lỗi không xác định trong QuizDetailView (GET): {e}", exc_info=True)
            return Response({"detail": f"Lỗi không xác định: {str(e)}"},
                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        Cập nhật (PATCH) một Quiz (Diff Engine C/U/D questions).
        View chỉ validate và ủy quyền.
        """
        
        # 1. Validate Input
        serializer = QuizCourseSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Convert sang Pydantic DTO (để lọc)
        try:
            # (Giả sử) QuizUpdateInput có các trường Optional
            update_dto = QuizUpdateInput(**validated_data)
            
            # --- ĐIỂM MẤU CHỐT CỦA PATCH ---
            # Chỉ lấy các trường user THỰC SỰ gửi lên
            patch_data = update_dto.model_dump(exclude_unset=True)
            
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. "No Updates" Check (Giống style của bạn)
        if not patch_data:
            try:
                instance = self.quiz_service.get_quiz_details(
                    quiz_id=pk, user=request.user
                )
                return Response({"instance": instance}, status=status.HTTP_200_OK)
            except (DomainError, ValueError) as e:
                return Response({"detail": f"Không tìm thấy quiz: {e}"}, status=status.HTTP_404_NOT_FOUND)

        # 4. Gọi Service "Diff Engine"
        try:
            updated_quiz = self.quiz_service.patch_quiz(
                quiz_id=pk,
                data=patch_data, # Dùng dict đã lọc
                user=request.user # Service sẽ check quyền
            )
            return Response({"instance": updated_quiz}, status=status.HTTP_200_OK)
        
        # 5. Error Handling (Bắt lỗi từ service)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong QuizDetailView (PATCH): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi cập nhật quiz."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        Xóa một Quiz.
        (Lưu ý: Cần xử lý logic ContentBlock trỏ đến nó)
        """
        try:
            # Ủy quyền toàn bộ cho service, bao gồm cả check quyền
            self.quiz_service.delete_quiz(
                quiz_id=pk, 
                user=request.user
            )
            
            # Service KHÔNG nên xóa nếu nó đang được 1 ContentBlock sử dụng.
            # Service nên ném DomainError nếu có.
            
            return Response(
                {"detail": f"Đã xóa thành công quiz (ID: {pk})."}, 
                status=status.HTTP_200_OK
                # (Hoặc 204 nếu bạn không muốn trả về body)
            )
        except DomainError as e: 
            # Bắt lỗi "Không tìm thấy" hoặc "Không thể xóa" (ví dụ: đang được dùng)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong QuizDetailView (DELETE): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi xóa quiz."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ======================================================================
# 2. VIEW (INSTRUCTOR)
# ======================================================================

class IntructorQuizDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /instructor/quizzes/<pk>/    - Lấy chi tiết 1 Quiz (cùng câu hỏi).
    PATCH /instructor/quizzes/<pk>/  - Cập nhật 1 Quiz (logic C/U/D lồng).
    DELETE /instructor/quizzes/<pk>/ - Xóa 1 Quiz.
    """
    # (Giả sử) Cần là Instructor (hoặc Admin) và service sẽ
    # kiểm tra quyền sở hữu (owner)
    permission_classes = [permissions.IsAuthenticated, IsInstructor] 

    # (Giả sử) DTO cho Output
    output_dto_admin = QuizAdminOutput
    output_dto_public = QuizInstructorOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_course_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Click 1 Quiz (Bao gồm cả 'questions') """
        try:
            # Service sẽ kiểm tra quyền (user) và trả về QuizDomain (đã lồng)
            quiz = self.quiz_service.get_quiz_details(
                quiz_id=pk, 
                user=request.user
            )
            return Response({"instance": quiz}, status=status.HTTP_200_OK)
        
        except DomainError as e: 
            # Bắt lỗi "Không tìm thấy" hoặc "Không có quyền" từ service
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Lỗi không xác định trong QuizDetailView (GET): {e}", exc_info=True)
            return Response({"detail": f"Lỗi không xác định: {str(e)}"},
                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        Cập nhật (PATCH) một Quiz (Diff Engine C/U/D questions).
        View chỉ validate và ủy quyền.
        """
        
        # 1. Validate Input
        serializer = QuizCourseSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Convert sang Pydantic DTO (để lọc)
        try:
            # (Giả sử) QuizUpdateInput có các trường Optional
            update_dto = QuizUpdateInput(**validated_data)
            
            # --- ĐIỂM MẤU CHỐT CỦA PATCH ---
            # Chỉ lấy các trường user THỰC SỰ gửi lên
            patch_data = update_dto.model_dump(exclude_unset=True)
            
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. "No Updates" Check (Giống style của bạn)
        if not patch_data:
            try:
                instance = self.quiz_service.get_quiz_details(
                    quiz_id=pk, user=request.user
                )
                return Response({"instance": instance}, status=status.HTTP_200_OK)
            except (DomainError, ValueError) as e:
                return Response({"detail": f"Không tìm thấy quiz: {e}"}, status=status.HTTP_404_NOT_FOUND)

        # 4. Gọi Service "Diff Engine"
        try:
            updated_quiz = self.quiz_service.patch_quiz(
                quiz_id=pk,
                data=patch_data, # Dùng dict đã lọc
                user=request.user # Service sẽ check quyền
            )
            return Response({"instance": updated_quiz}, status=status.HTTP_200_OK)
        
        # 5. Error Handling (Bắt lỗi từ service)
        except DomainError as e: 
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong QuizDetailView (PATCH): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi cập nhật quiz."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        Xóa một Quiz.
        (Lưu ý: Cần xử lý logic ContentBlock trỏ đến nó)
        """
        try:
            # Ủy quyền toàn bộ cho service, bao gồm cả check quyền
            self.quiz_service.delete_quiz(
                quiz_id=pk, 
                user=request.user
            )
            
            # Service KHÔNG nên xóa nếu nó đang được 1 ContentBlock sử dụng.
            # Service nên ném DomainError nếu có.
            
            return Response(
                {"detail": f"Đã xóa thành công quiz (ID: {pk})."}, 
                status=status.HTTP_200_OK
                # (Hoặc 204 nếu bạn không muốn trả về body)
            )
        except DomainError as e: 
            # Bắt lỗi "Không tìm thấy" hoặc "Không thể xóa" (ví dụ: đang được dùng)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong QuizDetailView (DELETE): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi xóa quiz."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)