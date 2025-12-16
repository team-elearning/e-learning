import logging
import uuid
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin
from core.api.permissions import CanViewCourseContent, IsAttemptOwner
from core.exceptions import DomainError
from quiz.models import Quiz
from progress.services import quiz_attempt_service, question_attempt_service
from progress.serializers import StartQuizInputSerializer
from progress.api.dtos.quiz_attempt_dto import QuizAttemptInfoOutput
from progress.api.dtos.question_attempt_dto import QuestionContentOutput
from progress.models import QuizAttempt



logger = logging.getLogger(__name__)

class QuizAttemptInitView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET quizzes/<quiz_id>/attempt/
    Chức năng: Bắt đầu làm bài hoặc Resume bài cũ. 
    Trả về ID bài làm và danh sách ID câu hỏi (để client tự loop gọi content)
    """
    permission_classes = [permissions.IsAuthenticated, CanViewCourseContent] # Học viên chỉ cần login

    permission_lookup = {'quiz_id': Quiz}

    output_dto_admin = QuizAttemptInfoOutput
    output_dto_public = QuizAttemptInfoOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = quiz_attempt_service

    def get(self, request, quiz_id: uuid.UUID, *args, **kwargs):
        """ Xem màn hình chờ (Info) """
        try:
            # 1. Gọi Service lấy Domain Data
            attempt_domain = self.service.start_or_resume_attempt(
                quiz_id=quiz_id, 
                user=request.user
            )
            return Response({"instance": attempt_domain}, status=status.HTTP_200_OK)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Lỗi hệ thống - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuizAttemptQuestionDetailView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET attempts/<attempt_id>/questions/<question_id>/
    Chức năng: Lấy nội dung của MỘT câu hỏi cụ thể (kèm options đã shuffle).
    """
    permission_classes = [permissions.IsAuthenticated, IsAttemptOwner]
    
    # Ở đây lookup theo attempt, cần check user sở hữu attempt đó (AutoPermissionCheckMixin lo hoặc view tự check)
    # permission_lookup = {'attempt_id': QuizAttempt} 

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


# class StartQuizAttemptView(RoleBasedOutputMixin, APIView):
#     """
#     POST /quiz/start/
#     """
#     permission_classes = [IsAuthenticated]
    
#     # Config Output DTO cho Mixin tự động map
#     output_dto_public = QuizAttemptPublicOutput
#     output_dto_admin = QuizAttemptAdminOutput 

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.quiz_service = quiz_progress_service # Inject Service

#     def post(self, request, *args, **kwargs):
#         # 1. Validate Input bằng Serializer
#         input_serializer = StartQuizInputSerializer(data=request.data)
#         try:
#             input_serializer.is_valid(raise_exception=True)
#             input_dto = StartQuizInput(**input_serializer.validated_data)
#         except Exception as e:
#             return Response({"detail": f"Dữ liệu không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             service_payload = input_dto.model_dump()

#             # 2. Gọi Service -> Nhận Domain Object
#             # View không cần biết logic tính remaining_seconds nữa
#             attempt_domain = self.quiz_service.start_quiz_attempt(
#                 user=request.user, 
#                 quiz_id=service_payload['quiz_id']
#             )

#             # 3. Trả về Response
#             # Key "instance" giúp RoleBasedOutputMixin hiểu cần serialize object này
#             return Response(
#                 {"instance": attempt_domain}, 
#                 status=status.HTTP_201_CREATED
#             )

#         except ValueError as e:
#             # Lỗi nghiệp vụ (Hết lượt, chưa mở đề...)
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
#         except Exception as e:
#             logger.error(f"Lỗi Start Quiz: {e}", exc_info=True)
#             return Response({"detail": f"Lỗi hệ thống - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)