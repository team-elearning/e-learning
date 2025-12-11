import boto3
import base64
import json
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from datetime import timedelta, datetime, timezone
from django.conf import settings

from media.models import UploadedFile



def generate_cloudfront_signed_url(object_key, expire_minutes=60):
    """
    Hàm sinh URL có chữ ký CloudFront.
    Input: object_key (VD: media/lesson/video.mp4)
    Output: https://d2t4....cloudfront.net/media/lesson/video.mp4?Policy=...&Signature=...
    """
    
    if not settings.MY_CLOUDFRONT_KEY_ID or not settings.MY_CLOUDFRONT_KEY_PATH:
        raise Exception("Server chưa cấu hình CloudFront Key ID hoặc Key Path!")
    
    # 1. Ghép URL gốc
    base_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{object_key}"
    
    # 2. Thời gian hết hạn (Ví dụ: 1 tiếng)
    expire_date = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    expire_timestamp = int(expire_date.timestamp())

    # 3. Tạo Policy (Luật cho phép truy cập)
    # Luật: Cho phép xem resource này nếu thời gian < expire_timestamp
    policy_dict = {
        "Statement": [{
            "Resource": base_url,
            "Condition": {
                "DateLessThan": {"AWS:EpochTime": expire_timestamp}
            }
        }]
    }
    policy_json = json.dumps(policy_dict, separators=(',', ':'))

    # 4. Đọc Private Key và Ký tên
    try:
        with open(settings.MY_CLOUDFRONT_KEY_PATH, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
    except FileNotFoundError:
        raise Exception(f"Không tìm thấy private key tại: {settings.MY_CLOUDFRONT_KEY_PATH}")

    # Ký Policy bằng thuật toán SHA1 (CloudFront yêu cầu)
    signature = private_key.sign(
        policy_json.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA1()
    )

    # 5. Mã hóa Base64 an toàn cho URL (Thay thế ký tự đặc biệt)
    def cloudfront_base64(data):
        return base64.b64encode(data).decode('utf-8').translate(str.maketrans('+=/', '-_~'))

    encoded_policy = cloudfront_base64(policy_json.encode('utf-8'))
    encoded_signature = cloudfront_base64(signature)
    
    # 6. Ghép thành URL cuối cùng
    signed_url = f"{base_url}?Policy={encoded_policy}&Signature={encoded_signature}&Key-Pair-Id={settings.MY_CLOUDFRONT_KEY_ID}"
    
    return signed_url


def get_signed_url_by_id(file_id: str, expire_minutes=60) -> str:
    """
    Hàm tiện ích: Nhận vào UUID, trả về CloudFront Signed URL.
    Dùng cho các module khác (Content, Quiz) gọi sang.
    """
    if not file_id:
        return None
        
    try:
        # 1. Query nhẹ vào DB để lấy đường dẫn S3 (file.name)
        # Chỉ lấy trường 'file' để tối ưu query
        file_obj = UploadedFile.objects.only('file').get(id=file_id)
        
        # 2. Lấy S3 Key (VD: media/images/2025/abc.jpg)
        s3_key = file_obj.file.name
        
        # 3. Ký tên
        return generate_cloudfront_signed_url(s3_key, expire_minutes=expire_minutes)
        
    except UploadedFile.DoesNotExist:
        return None 
    except Exception as e:
        print(f"Error resolving URL for {file_id}: {e}")
        return None
    

def s3_copy_object(src_path, dest_path, is_public=True):
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None) # Nếu dùng MinIO/DigitalOcean
    )
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    # Cấu hình ACL
    extra_args = {'ACL': 'public-read'} if is_public else {'ACL': 'private'}

    # Lệnh Copy nội bộ trên Cloud (Cực nhanh)
    s3.copy_object(
        Bucket=bucket_name,
        CopySource={'Bucket': bucket_name, 'Key': src_path},
        Key=dest_path,
        **extra_args
    )

    # (Tùy chọn) Xóa file gốc ở Staging luôn để dọn rác
    s3.delete_object(Bucket=bucket_name, Key=src_path)