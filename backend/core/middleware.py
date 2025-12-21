import logging
import traceback
import threading
from django.http import JsonResponse



logger = logging.getLogger(__name__)

class GlobalExceptionMiddleware:
    """Catch all unexpected exceptions at the middleware level."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            logger.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
            return JsonResponse({
                "error": "Internal Server Error",
                "detail": str(e)
            }, status=500)
        

_thread_locals = threading.local()

def get_current_request_context():
    """Hàm helper để lấy context ở bất kỳ đâu"""
    return getattr(_thread_locals, 'context', {})

class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Extract Info
        ip = self._get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')
        
        # 2. Save to Thread Local
        _thread_locals.context = {
            'ip': ip,
            'user_agent': ua,
            # Có thể lưu thêm user_id nếu muốn dùng cho Signals
        }

        response = self.get_response(request)
        
        # 3. Cleanup (Quan trọng để tránh memory leak)
        _thread_locals.context = {}
        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip