from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import logging

# Import các mixins của bạn
from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin
from media.services import cloud_service
from media.api.dtos.cloud_dto import MediaCookieOutput

logger = logging.getLogger(__name__)

class CloudFrontCookieView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    POST /cookies/
    Cấp quyền truy cập file Private (Ảnh/Video) thông qua CloudFront Signed Cookies.
    """
    permission_classes = [IsAuthenticated]
    
    # Cookie Auth là logic chung, không cần lookup object cụ thể
    permission_lookup = {} 

    # Dù trả về cookie header là chính, nhưng body vẫn có thể dùng DTO nếu muốn chuẩn hóa
    # Ở đây mình để None hoặc default vì body chỉ mang tính thông báo
    output_dto_public = MediaCookieOutput 
    output_dto_instructor = MediaCookieOutput
    output_dto_admin = MediaCookieOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.media_service = cloud_service

    def post(self, request, *args, **kwargs):
        """ Refresh cookies cho session làm việc """
        try:
            # 1. Gọi Service Logic
            result = self.media_service.generate_access_cookies()
            
            cookie_values = result['cookies']
            metadata = result['metadata']

            # 2. Tạo Response Body (Thông báo cho FE biết bao giờ hết hạn)
            response = Response(
                {"instance": metadata}, 
                status=status.HTTP_200_OK
            )

            # 3. Set Cookies vào Header (Side-effect)
            # Lấy domain cookie từ settings (quan trọng để sub-domain api set được cho cdn)
            # VD: .school.com (có dấu chấm ở đầu)
            cookie_domain = getattr(settings, 'CLOUDFRONT_COOKIE_DOMAIN', None) 
            
            for key, value in cookie_values.items():
                response.set_cookie(
                    key=key,
                    value=value,
                    domain=cookie_domain,
                    secure=True,       # Bắt buộc HTTPS
                    httponly=True,     # Bảo mật: JS không đọc được
                    samesite='None',   # Cho phép Cross-site (API -> CDN)
                    max_age=metadata['expires_in_seconds']
                )

            return response

        except ValueError as e:
            # Lỗi cấu hình hoặc input (Service raise)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # Lỗi không xác định
            logger.error(f"Lỗi cấp CloudFront Cookie: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống khi cấp quyền media."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)