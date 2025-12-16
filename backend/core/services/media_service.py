from django.conf import settings
from typing import Any



def recursive_inject_cdn_url(data: Any) -> Any:
    """
    Duyệt JSON đệ quy để tìm file object và ghép Clean URL CloudFront.
    Dùng chung cho cả Admin View và Student View.
    """
    if isinstance(data, dict):
        # Check nếu dict này là một File Object (theo cấu trúc hệ thống file của bạn)
        if data.get('storage_type') == 's3_private' and 'file_path' in data:
            new_file_data = data.copy()
            cdn_domain = settings.AWS_S3_CUSTOM_DOMAIN
            # Ghép URL: https://cdn.school.com/private/path/to/file.jpg
            new_file_data['url'] = f"https://{cdn_domain}/private/{data['file_path']}"
            return new_file_data

        # Duyệt tiếp các key con
        return {k: recursive_inject_cdn_url(v) for k, v in data.items()}

    elif isinstance(data, list):
        return [recursive_inject_cdn_url(item) for item in data]

    return data