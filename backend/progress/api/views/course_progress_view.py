import logging
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView

from core.exceptions import DomainError
from progress.services import course_progress_service



logger = logging.getLogger(__name__)

class CourseProgressView(APIView):
    """
    GET /courses/<pk>/
    - Lấy % hoàn thành và trạng thái chung của user tại khóa học <pk>.
    """
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Giả định bạn đã có course_progress_service
        self.course_progress_service = course_progress_service 

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        try:
            # Service trả về CourseProgressDomain (chứa percent, last_accessed...)
            progress_domain = self.course_progress_service.get_course_progress_summary(
                user=request.user,
                course_id=pk
            )
            return Response({"instance": progress_domain}, status=status.HTTP_200_OK)

        except DomainError as e:
            # Ví dụ: User chưa enroll khóa này nên chưa có progress
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Lỗi trong CourseProgressView (GET): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
