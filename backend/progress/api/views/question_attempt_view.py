import logging
import uuid
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin
from core.api.permissions import CanViewCourseContent, IsAttemptOwner
from core.exceptions import DomainError
from quiz.models import Quiz
from progress.services import quiz_attempt_service, question_attempt_service
from progress.serializers import StartQuizInputSerializer
from progress.api.dtos.quiz_attempt_dto import QuizAttemptInfoOutput
from progress.api.dtos.question_attempt_dto import QuestionSubmissionInput, QuestionContentOutput, QuestionSubmissionOutput
from progress.models import QuizAttempt
from progress.serializers import QuestionAnswerInputSerializer



logger = logging.getLogger(__name__)

class AttemptQuestionDetailView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET attempts/<attempt_id>/questions/<question_id>/
    Chức năng: Lấy nội dung của MỘT câu hỏi cụ thể (kèm options đã shuffle).
    """
    permission_classes = [permissions.IsAuthenticated, IsAttemptOwner]
    
    # Ở đây lookup theo attempt, cần check user sở hữu attempt đó (AutoPermissionCheckMixin lo hoặc view tự check)
    permission_lookup = {'attempt_id': QuizAttempt} 

    output_dto_public = QuestionContentOutput
    output_dto_admin = QuestionContentOutput

    permission_lookup = {'attempt_id': QuizAttempt}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = question_attempt_service

    def get(self, request, attempt_id: uuid.UUID, question_id: uuid.UUID, *args, **kwargs):
        try:
            # Service trả về QuestionContentDomain
            question_domain = self.service.get_question_in_attempt(
                attempt_id=attempt_id,
                question_id=question_id,
                user=request.user
            )
            return Response({"instance": question_domain}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        

class AttemptQuestionSaveDraftView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    PUT attempts/<attempt_id>/questions/<question_id>/draft/
    Chức năng: Autosave câu trả lời (Không chấm điểm).
    """
    permission_classes = [permissions.IsAuthenticated, IsAttemptOwner]
    
    # AutoPermissionCheckMixin sẽ check user có sở hữu attempt_id không
    permission_lookup = {'attempt_id': QuizAttempt} 

    # Autosave thường không cần Output DTO phức tạp, chỉ cần báo thành công
    # Nhưng nếu cần trả về data mới nhất, có thể dùng lại Serializer nào đó
    output_dto_public = None 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = question_attempt_service # Service chứa hàm save_question_draft

    def put(self, request, attempt_id: uuid.UUID, question_id: uuid.UUID, *args, **kwargs):
        # 1. Serializer (Validate Body)
        serializer = QuestionAnswerInputSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Map to Input DTO
        # Ghép question_id từ URL và answer_data từ Body vào DTO
        try:
            submission_dto = QuestionSubmissionInput(
                answer_data=serializer.validated_data['answer_data']
            )
        except Exception as e:
             return Response({"detail": f"Dữ liệu không hợp lệ: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Call Service
        try:
            # Service trả về True/False
            self.service.save_question_draft(
                attempt_id=attempt_id,
                question_id=question_id,
                submission_data=submission_dto.to_dict(),
                user=request.user
            )
            
            # 4. Response
            return Response({"detail": "Đã lưu nháp thành công."}, status=status.HTTP_200_OK)

        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi Autosave: {e}", exc_info=True)
            return Response({"detail": f"Lỗi hệ thống - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AttemptQuestionSubmitView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    POST attempts/<attempt_id>/questions/<question_id>/submit/
    Chức năng: Nộp bài một câu hỏi -> Chấm điểm -> Trả về kết quả.
    """
    permission_classes = [permissions.IsAuthenticated, IsAttemptOwner]
    permission_lookup = {'attempt_id': QuizAttempt}

    # Định nghĩa Output DTO để Mixin tự động serialize domain trả về
    output_dto_public = QuestionSubmissionOutput
    output_dto_admin = QuestionSubmissionOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = question_attempt_service

    def post(self, request, attempt_id: uuid.UUID, question_id: uuid.UUID, *args, **kwargs):
        # 1. Serializer (Validate Body)
        serializer = QuestionAnswerInputSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Map to Input DTO
        try:
            submission_dto = QuestionSubmissionInput(
                answer_data=serializer.validated_data['answer_data']
            )
        except Exception as e:
            return Response({"detail": f"Input data error - {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Call Service -> Trả về Domain Object
        try:
            submission_domain = self.service.submit_question(
                attempt_id=attempt_id,
                submission=submission_dto,
                user=request.user
            ) 
            return Response({"instance": submission_domain}, status=status.HTTP_200_OK)
            
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi Submit Question: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)