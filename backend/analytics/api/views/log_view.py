from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
from pydantic import ValidationError as PydanticValidationError
import logging

from analytics.api.dtos.log_dto import ActivityBatchInput
from analytics.serializers import ActivityBatchSerializer
from analytics.services.log_service import record_batch



logger = logging.getLogger(__name__)

class AnalyticsBatchView(APIView):
    """
    POST /api/analytics/batch/
    Endpoint nhận log hàng loạt (Heartbeat, Scroll tracking...).
    Xử lý Async thông qua Celery.
    """
    permission_classes = [IsAuthenticated] # Bắt buộc phải login

    def post(self, request, *args, **kwargs):
        # 1. DRF Serializer Validation
        serializer = ActivityBatchSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        # 2. Convert to Pydantic DTO (Strict Type Checking)
        try:
            batch_dto = ActivityBatchInput(**validated_data)
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Call Service
        try:
            # Chuyển đổi list Pydantic object thành list dict thuần để service xử lý
            # logic: [item.model_dump() for item in batch_dto.batch]
            data_list_dict = [item.model_dump() for item in batch_dto.batch]

            is_processed = record_batch(
                user=request.user,
                data_list=data_list_dict
            )

            if is_processed:
                return Response(
                    {"detail": "Đã tiếp nhận log thành công."}, 
                    status=status.HTTP_200_OK
                )
            else:
                # Trường hợp data_list rỗng hoặc bị filter hết do invalid action
                return Response(
                    {"detail": "Không có dữ liệu hợp lệ nào được ghi nhận."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Lỗi trong AnalyticsBatchView (POST): {e}", exc_info=True)
            return Response(
                {"detail": f"Lỗi máy chủ khi xử lý log - {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )