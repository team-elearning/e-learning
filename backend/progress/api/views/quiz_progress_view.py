import logging
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView

from core.exceptions import DomainError
from backend.progress.services import quiz_progress_service



logger = logging.getLogger(__name__)

class QuizSubmissionView(APIView):
    """
    POST /quizzes/<pk>/submit/ - Nộp bài Quiz & Chấm điểm.
    """
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Có thể dùng quiz_service hoặc tracking_service tùy cách bạn tổ chức
        self.quiz_progress_service = quiz_progress_service 

    def post(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        Body: {
            "answers": [
                {"question_id": "q1", "selected_options": ["a"]},
                {"question_id": "q2", "text": "hello"}
            ]
        }
        """
        serializer = QuizSubmissionSerializer(data=request.data)
        # ... validate serializer ... (như trên)

        try:
            # Service sẽ:
            # 1. Tính điểm từng câu.
            # 2. Lưu QuizAttempt.
            # 3. Nếu điểm > pass_grade -> Update ngược lại BlockCompletion = True.
            result_domain = self.quiz_progress_service.submit_quiz_attempt(
                user=request.user,
                quiz_id=pk,
                answers=serializer.validated_data['answers']
            )
            
            return Response({"instance": result_domain}, status=status.HTTP_200_OK)

        except DomainError as e:
             # Ví dụ: Hết giờ làm bài, hoặc quiz đã đóng
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi QuizSubmissionView: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)