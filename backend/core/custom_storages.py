from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings



def get_cloudfront_key_data():
        # Đọc từ tên biến MỚI
        key_path = getattr(settings, 'MY_CLOUDFRONT_KEY_PATH', None)
        if key_path and key_path.exists():
            try:
                with open(key_path, 'rb') as f:
                    return f.read()
            except Exception:
                pass
        return None


class PublicMediaStorage(S3Boto3Storage):
    location = 'public'
    default_acl = 'public-read'
    file_overwrite = False
    querystring_auth = False # <--- QUAN TRỌNG: Tắt chữ ký cho kho này
    
    # --- QUAN TRỌNG: Ghi đè thành None để tránh lỗi ---
    # Public Storage không bao giờ cần ký tên, nên set None để
    # django-storages không validate cặp key này.
    cloudfront_key_id = None
    cloudfront_key = None


class PrivateMediaStorage(S3Boto3Storage):
    location = 'private' # Lưu vào folder /private trên S3
    default_acl = 'private'
    file_overwrite = False
    # custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    querystring_auth = True # <--- Bật chữ ký bảo mật

    def __init__(self, *args, **kwargs):
        # --- 3. NẠP THỦ CÔNG TỪ BIẾN ĐÃ ĐỔI TÊN ---
        self.cloudfront_key_id = getattr(settings, 'MY_CLOUDFRONT_KEY_ID', None)
        self.cloudfront_key = get_cloudfront_key_data()
        
        super().__init__(*args, **kwargs)


    