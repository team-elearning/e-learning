import logging
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError as DRFValidationError
from pydantic import ValidationError as PydanticValidationError

from content.services.exceptions import DomainError
from content.serializers import QuizPatchInputSerializer
from content.api.dtos.quiz_dto import QuizUpdateInput, QuizPublicOutput, QuizAdminOutput
from content.services import quiz_service
from content.api.permissions import IsInstructor
from content.api.mixins import RoleBasedOutputMixin 

logger = logging.getLogger(__name__)

# ======================================================================
# 1. LIST VIEW (Chỉ Admin)
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
        self.quiz_service = quiz_service

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



# ======================================================================
# 2. DETAIL VIEW (GET / PATCH / DELETE)
# ======================================================================

class IntructorQuizDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /api/quizzes/<pk>/    - Lấy chi tiết 1 Quiz (cùng câu hỏi).
    PATCH /api/quizzes/<pk>/  - Cập nhật 1 Quiz (logic C/U/D lồng).
    DELETE /api/quizzes/<pk>/ - Xóa 1 Quiz.
    """
    # (Giả sử) Cần là Instructor (hoặc Admin) và service sẽ
    # kiểm tra quyền sở hữu (owner)
    permission_classes = [permissions.IsAuthenticated, IsInstructor] 

    # (Giả sử) DTO cho Output
    output_dto_admin = QuizAdminOutput
    output_dto_public = QuizPublicOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        """ LClick 1 Quiz (Bao gồm cả 'questions') """
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
        
        # 1. Validate Input bằng DRF Serializer
        # (Serializer này không phải ModelSerializer, không cần instance)
        serializer = QuizPatchInputSerializer(data=request.data)
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