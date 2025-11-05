from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import traceback
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Global exception handler:
    - Chuyển 500 thành lỗi có cấu trúc.
    - Log chi tiết server-side, trả JSON nhẹ cho client.
    """
    # Gọi handler mặc định trước (bắt các lỗi DRF như ValidationError)
    response = exception_handler(exc, context)

    if response is not None:
        # Giữ nguyên format mặc định cho lỗi chuẩn của DRF
        return response

    # Xử lý lỗi không bắt được (500)
    view = context.get('view', None)
    view_name = view.__class__.__name__ if view else 'unknown view'

    # Log chi tiết vào file server (chỉ dev mới thấy)
    logger.error(
        f"[{view_name}] Unhandled exception: {exc}\n{traceback.format_exc()}"
    )

    # Trả về JSON nhẹ cho FE
    return Response(
        {
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
