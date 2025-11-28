# domain/files.py
from dataclasses import dataclass
from typing import Dict, Any
import uuid

@dataclass
class PresignedUploadDomain:
    """
    Domain object chứa thông tin xác thực để Client thực hiện upload lên S3.
    Object này không đại diện cho Record trong DB, mà đại diện cho "Vé thông hành".
    """
    file_id: uuid.UUID
    upload_url: str
    upload_fields: Dict[str, Any]