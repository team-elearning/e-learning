import logging
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError as DRFValidationError

from core.exceptions import DomainError
from progress.services import lesson_progress_service



logger = logging.getLogger(__name__)

class LessonProcessView(APIView):
    """
    GET  /lessons/<pk>/ - Lấy trạng thái các block trong lesson.
    POST /lessons/<pk>/sync/ - Cập nhật tiến độ (Heartbeat).
    """
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lesson_progress_service = lesson_progress_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        Lấy danh sách trạng thái (BlockCompletion) của lesson <pk>.
        Frontend dùng data này để map vào ContentBlock (hiển thị tick xanh, resume video).
        """
        try:
            # Trả về List[BlockCompletionDomain]
            block_statuses = self.lesson_progress_service.get_lesson_block_statuses(
                user=request.user,
                lesson_id=pk
            )
            return Response({"instance": block_statuses}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Lỗi LessonTrackingView (GET): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, pk: uuid.UUID, *args, **kwargs):
        """
        API Sync (Heartbeat): Gọi liên tục hoặc khi user pause video/chuyển bài.
        Body: {
            "block_id": "uuid...",
            "is_completed": true,
            "interaction_data": {"timestamp": 120} 
        }
        """
        # 1. Validate Input (Giả định có Serializer)
        serializer = TrackingSyncSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            payload = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Gọi Service xử lý logic tracking
        try:
            updated_status = self.lesson_progress_service.sync_block_progress(
                user=request.user,
                lesson_id=pk,
                block_id=payload['block_id'],
                is_completed=payload.get('is_completed', False),
                interaction_data=payload.get('interaction_data', {})
            )
            
            return Response({"instance": updated_status}, status=status.HTTP_200_OK)

        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi LessonTrackingView (POST Sync): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)