from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from pydantic import ValidationError as PydanticValidationError

from core.api.permissions import IsInstructor, IsQuizOwner
from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin
from quiz.api.dtos.question_dto import QuestionInput, QuestionAdminOutput, QuestionInstructorOutput, QuestionPublicOutput
from quiz.serializers import QuestionInputSerializer
from quiz.services import question_service
from quiz.models import Quiz, Question



class InstructorQuestionListView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    Quản lý câu hỏi bên trong một Quiz cụ thể.
    ENDPOINT: /instructor/quizzes/<quiz_id>/questions/
    
    (Lưu ý: quiz_id ở đây có thể là ID của Exam hoặc Practice)
    """
    permission_classes = [IsAuthenticated, IsInstructor, IsQuizOwner]

    permission_lookup = {'quiz_id': Quiz}

    output_dto_admin = QuestionAdminOutput
    output_dto_instructor = QuestionInstructorOutput
    output_dto_public = QuestionPublicOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question_service = question_service

    def get(self, request, quiz_id, *args, **kwargs):
        """ Lấy danh sách câu hỏi của Quiz này (kèm prompt, options) """
        try:
            questions = self.question_service.list_questions_for_quiz(
                quiz_id=quiz_id
            )
            # Trả về list DTO chứa prompt, answer_payload đầy đủ để Frontend render form
            return Response({"instance": questions}, status=status.HTTP_200_OK)
        except Exception as e:
             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, quiz_id, *args, **kwargs):
        """
        Thêm câu hỏi mới vào Quiz.
        Payload mẫu cho field 'prompt' (JSON):
        {
            "type": "multiple_choice_single",
            "prompt": {
                "text": "Thủ đô của Việt Nam là gì?",
                "options": [
                     {"id": "A", "text": "Hà Nội"},
                     {"id": "B", "text": "HCM"}
                ]
            },
            "answer_payload": { "correct_ids": ["A"] },
            "score": 1.0
        }
        """
        serializer = QuestionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # (Giả sử) QuizUpdateInput có các trường Optional
            update_dto = QuestionInput(**serializer.validated_data)
            
            # --- ĐIỂM MẤU CHỐT CỦA PATCH ---
            # Chỉ lấy các trường user THỰC SỰ gửi lên
            patch_data = update_dto.model_dump(exclude_unset=True)
            
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Service cần handle việc parse JSON prompt vào model Question
            new_question = self.question_service.create_question(
                quiz_id=quiz_id,
                data=patch_data
            )
            return Response({"instance": new_question}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class InstructorQuestionDetailView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    Sửa/Xóa từng câu hỏi cụ thể.
    ENDPOINT: /instructor/questions/<question_id>/
    """
    # 1. Config Permissions
    # Lưu ý: IsQuizOwner cần hỗ trợ check obj.quiz.owner nếu obj là Question
    permission_classes = [IsAuthenticated, IsInstructor, IsQuizOwner]
    
    # Lookup object để check quyền (dựa vào URL param 'question_id')
    permission_lookup = {'question_id': Question}

    # 2. Config Output DTO (RoleBasedOutputMixin)
    output_dto_admin = QuestionAdminOutput
    output_dto_instructor = QuestionInstructorOutput
    output_dto_public = QuestionPublicOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question_service = question_service

    def get(self, request, question_id, *args, **kwargs):
        """ Lấy chi tiết nội dung câu hỏi """
        try:
            question = self.question_service.get_question_detail(question_id=question_id)
            
            # Trả về object Domain, Mixin sẽ tự convert sang output_dto_instructor
            return Response({"instance": question}, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, question_id, *args, **kwargs):
        """ 
        Update nội dung câu hỏi (Sửa prompt, options, cấu hình).
        Hỗ trợ partial update (gửi trường nào sửa trường đó).
        """
        # Cho phép partial=True để user không phải gửi lại toàn bộ cục json
        serializer = QuestionInputSerializer(data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate Pydantic & Dump data
            update_dto = QuestionInput(**serializer.validated_data)
            # exclude_unset=True cực quan trọng để không overwrite các field cũ bằng None
            patch_data = update_dto.model_dump(exclude_unset=True)

            # Gọi Service
            updated_question = self.question_service.update_question(
                question_id=question_id,
                data=patch_data
            )

            # Trả về Response, Mixin sẽ tự convert sang InstructorOutput JSON
            return Response({"instance": updated_question}, status=status.HTTP_200_OK)

        except (PydanticValidationError, ValueError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log lỗi server (nếu cần)
            return Response({"detail": f"Lỗi hệ thống khi cập nhật câu hỏi - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, question_id, *args, **kwargs):
        """ Xóa câu hỏi khỏi đề """
        try:
            self.question_service.delete_question(question_id=question_id)
            return Response(
                {"detail": "Xóa câu hỏi thành công"},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)