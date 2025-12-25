from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from pydantic import ValidationError as PydanticValidationError
import logging

from core.api.mixins import AutoPermissionCheckMixin, RoleBasedOutputMixin
from core.api.permissions import IsInstructor
from content.models import Course
from analytics.api.dtos.analytics_dto import CourseHealthAnalyzeInput, AnalysisResultOutput
from analytics.serializers import CourseHealthAnalyzeSerializer
from analytics.services import analytics_service  
from analytics.tasks import async_analyze_course



logger = logging.getLogger(__name__)

class CourseHealthAnalyzeView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    POST /instructor/courses/<course_id>/analyze/
    Endpoint để Instructor kích hoạt phân tích rủi ro thủ công (On-demand).
    """
    permission_classes = [IsInstructor] 
    
    # AutoPermissionCheckMixin sẽ tự động check:
    # 1. course_id trong URL có tồn tại không?
    # 2. request.user có phải owner của course này không?
    permission_lookup = {'course_id': Course} 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics_service = analytics_service

    def post(self, request, course_id, *args, **kwargs):
        """
        Trigger phân tích sức khỏe lớp học.
        Flow: Serializer -> Input DTO -> Service -> Domain -> Output DTO
        """
        
        # 1. Serializer: Validate Body Request
        serializer = CourseHealthAnalyzeSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Input DTO: Convert dữ liệu sạch sang DTO
        try:
            input_dto = CourseHealthAnalyzeInput(**validated_data)
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Service Call: Truyền tham số vào Service
        try:
            async_analyze_course.delay(str(course_id))
            
            # Lưu ý: Nếu service chạy Async (Celery), result_domain có thể chỉ là thông báo "Task Started"
            # Nếu chạy Sync (như code mẫu trước), nó là kết quả thật.
            return Response(
                {
                    "detail": "Yêu cầu phân tích đã được tiếp nhận và đang chạy ngầm.",
                    "status": "processing"
                }, 
                status=status.HTTP_202_ACCEPTED
            )

        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong CourseHealthAnalyzeView (POST): {e}", exc_info=True)
            return Response({"detail": f"Lỗi máy chủ khi phân tích - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
