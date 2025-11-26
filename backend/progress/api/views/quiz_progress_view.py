from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging

from core.api.mixins import RoleBasedOutputMixin
from progress.services import quiz_progress_service
from progress.serializers import StartQuizInputSerializer
from progress.api.dtos.quiz_attempt_dto import QuizAttemptAdminOutput, QuizAttemptPublicOutput, StartQuizInput



logger = logging.getLogger(__name__)

class StartQuizAttemptView(RoleBasedOutputMixin, APIView):
    """
    POST /quiz/start/
    """
    permission_classes = [IsAuthenticated]
    
    # Config Output DTO cho Mixin tự động map
    output_dto_public = QuizAttemptPublicOutput
    output_dto_admin = QuizAttemptAdminOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_progress_service # Inject Service

    def post(self, request, *args, **kwargs):
        # 1. Validate Input bằng Serializer
        input_serializer = StartQuizInputSerializer(data=request.data)
        try:
            input_serializer.is_valid(raise_exception=True)
            input_dto = StartQuizInput(**input_serializer.validated_data)
        except Exception as e:
            return Response({"detail": f"Dữ liệu không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service_payload = input_dto.model_dump()

            # 2. Gọi Service -> Nhận Domain Object
            # View không cần biết logic tính remaining_seconds nữa
            attempt_domain = self.quiz_service.start_quiz_attempt(
                user=request.user, 
                quiz_id=service_payload['quiz_id']
            )

            # 3. Trả về Response
            # Key "instance" giúp RoleBasedOutputMixin hiểu cần serialize object này
            return Response(
                {"instance": attempt_domain}, 
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            # Lỗi nghiệp vụ (Hết lượt, chưa mở đề...)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Lỗi Start Quiz: {e}", exc_info=True)
            return Response({"detail": f"Lỗi hệ thống - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)