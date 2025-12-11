import uuid
from bs4 import BeautifulSoup
from django.conf import settings
from typing import Optional, List, Dict, Any

from core.exceptions import DomainValidationError
from content.models import ContentBlock
from media.services.cloud_service import get_signed_url_by_id, generate_cloudfront_signed_url



class ContentBlockDomain:
    """
    Domain object cho ContentBlock.
    Đã đồng bộ hóa validation với Serializer.
    """

    # --- SỬA 1: Thêm các type mới ---
    VALID_TYPES = (
        'rich_text', 'video', 'quiz', 'pdf', 
        'docx', 'file', 'audio'
    )
    
    # (Bạn có thể giữ lại các hằng số MAX_LENGTH...)

    def __init__(self, type: str, lesson_id: str, position: int = 0, title: str = None, payload: Optional[Dict[str, Any]] = None, id: Optional[str] = None, icon_key: Optional[Dict[str, Any]] = None):
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.lesson_id = lesson_id 
        self.type = type
        self.position = int(position)
        self.payload = payload or {}
        self.icon_key = icon_key or {}
        
        # Chạy validate
        self.validate_basic()
        # self.validate_payload() # Nên validate cả payload khi khởi tạo

    def validate_basic(self):
        """Validate các trường cơ bản."""
        if not self.lesson_id:
            raise DomainValidationError("ContentBlock.lesson_id required.")
        if self.type not in self.VALID_TYPES:
            raise DomainValidationError(f"Invalid ContentBlock type: {self.type}")
        if self.position < 0:
            raise DomainValidationError("ContentBlock.position must be >= 0")

    def validate_payload(self):
        """
        --- SỬA 2: Viết lại toàn bộ để khớp với JSON/Serializer ---
        Validate payload dựa trên 'type'.
        """
        # text
        if self.type == "text":
            if "text" not in self.payload:
                raise DomainValidationError("Payload 'text' phải có 'text' field.")
        
        # image
        elif self.type == "image":
            if "image_id" not in self.payload:
                raise DomainValidationError("Payload 'image' phải có 'image_id'.")

        # video
        elif self.type == "video":
            if "video_id" not in self.payload:
                raise DomainValidationError("Payload 'video' phải có 'video_id'.")

        # pdf / docx
        elif self.type in ("pdf", "docx"):
            if "file_id" not in self.payload:
                raise DomainValidationError(f"Payload '{self.type}' phải có 'file_id'.")

        # quiz
        elif self.type == "quiz":
            if "quiz_id" not in self.payload:
                raise DomainValidationError("Payload 'quiz' phải có 'quiz_id'.")
        
        # exploration_ref
        elif self.type == "exploration_ref":
            if "exploration_id" not in self.payload:
                raise DomainValidationError("exploration_ref must include exploration_id.")
        
        # (Không cần else, vì validate_basic đã bắt type không hợp lệ)
        return True

    def to_dict(self):
        return {"id": self.id, "lesson_id": self.lesson_id, "type": self.type, "position": self.position, "payload": self.payload}

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position,
            "payload": self.payload 
        }

    @staticmethod
    def _map_icon(block_type):
        """Helper để frontend biết hiển thị icon gì"""
        icons = {
            'video': 'play-circle',
            'quiz': 'help-circle',
            'pdf': 'file-text',
            'docx': 'file-text',
            'file': 'file',
            'rich_text': 'align-left',
        }
        return icons.get(block_type, 'box')

    # @staticmethod
    # def _process_payload_heavy(model):
    #     """
    #     Logic xử lý nặng:
    #     1. Tạo Signed URL từ file_path (cho Video/PDF Private).
    #     2. Rich Text: Giữ nguyên HTML (Vì ảnh đã được xử lý thành Public URL lúc Save rồi).
    #     """
    #     # Copy payload để không ảnh hưởng object gốc
    #     processed_payload = model.payload.copy() if model.payload else {}
        
    #     try:
    #         # -------------------------------------------------------
    #         # CASE 1: CÁC LOẠI FILE PRIVATE (Video, PDF, Audio)
    #         # -------------------------------------------------------
    #         # Service đã lưu: 'file_path': 'courses/123/lessons/456/block_789.mp4'
    #         if 'file_path' in processed_payload:
    #             path = processed_payload['file_path']

    #             # QUAN TRỌNG: Phải ghép prefix 'private/' vào nếu CloudFront map full bucket
    #             full_s3_key = f"private/{path}"
                
    #             # Gọi hàm ký tên URL dựa trên PATH (Không phải ID)
    #             # Hàm này dùng thư viện cloudfront signer hoặc s3 signer
    #             # Ví dụ: trả về https://cdn.lms.com/private/courses/...?Signature=...
    #             signed_url = generate_cloudfront_signed_url(full_s3_key, expire_minutes=360) 
                
    #             # Gán URL vào để frontend dùng
    #             processed_payload['url'] = signed_url

    #         # -------------------------------------------------------
    #         # CASE 2: RICH TEXT (Đơn giản hóa)
    #         # -------------------------------------------------------
    #         # Với cách mới, ảnh trong bài viết (Rich Text) nên được lưu Public.
    #         # Lúc lưu (Service), ta đã replace ID bằng URL public rồi.
    #         # Nên lúc Read (Domain), ta KHÔNG CẦN LÀM GÌ CẢ.
    #         elif model.type == 'rich_text':
    #             pass # HTML đã có sẵn src="https://cdn..." rồi.

    #         # -------------------------------------------------------
    #         # CASE 3: QUIZ
    #         # -------------------------------------------------------
    #         elif model.type == 'quiz':
    #              if model.quiz_ref_id:
    #                 processed_payload['quiz_id'] = str(model.quiz_ref_id)

    #     except Exception as e:
    #         # Logger nên được inject vào đây thay vì print
    #         print(f"Error processing payload for block {model.id}: {e}")
    #         pass

    #     return processed_payload

    @staticmethod
    def _process_payload_heavy(model):
        """
        Logic xử lý Payload cho Content Block (Video/PDF/RichText).
        Bây giờ chỉ cần ghép URL CDN vì Browser đã có Cookie.
        """
        processed_payload = model.payload.copy() if model.payload else {}
        cdn_domain = settings.AWS_S3_CUSTOM_DOMAIN # VD: cdn.school.com
        
        try:
            # -------------------------------------------------------
            # CASE 1: CÁC LOẠI FILE PRIVATE (Video, PDF, Audio)
            # -------------------------------------------------------
            if 'file_path' in processed_payload and processed_payload.get('storage_type') == 's3_private':
                path = processed_payload['file_path']
                
                # Logic cũ: generate_signed_url(...) -> XÓA
                
                # Logic mới: Clean URL
                # Kết quả: https://cdn.school.com/private/courses/123/video.mp4
                processed_payload['url'] = f"https://{cdn_domain}/private/{path}"

            # -------------------------------------------------------
            # CASE 2: RICH TEXT (HTML Content)
            # -------------------------------------------------------
            elif model.type == 'rich_text':
                # Nếu trong HTML lưu đường dẫn tương đối (VD: src="courses/...")
                # Ta cần thêm prefix domain vào.
                html = processed_payload.get('html_content', '')
                
                # Hàm helper đơn giản để replace (hoặc dùng BeautifulSoup nếu cần chuẩn xác)
                # Giả sử DB lưu: src="courses/uuid/img.jpg"
                # Cần ra: src="https://cdn.../private/courses/uuid/img.jpg"
                prefix = f"https://{cdn_domain}/private/"
                
                # Replace đơn giản các đường dẫn tương đối (tùy vào cách bạn lưu lúc upload)
                if html and 'src="courses/' in html:
                    processed_payload['html_content'] = html.replace('src="courses/', f'src="{prefix}courses/')

            # -------------------------------------------------------
            # CASE 3: QUIZ
            # -------------------------------------------------------
            elif model.type == 'quiz':
                 if model.quiz_ref_id:
                    processed_payload['quiz_id'] = str(model.quiz_ref_id)

        except Exception as e:
            # Nên dùng logger thật thay vì print
            print(f"Error processing payload for block {model.id}: {e}")
            pass

        return processed_payload

    @classmethod
    def from_model_summary(cls, model):
        """Dùng cho Syllabus/List: Chỉ lấy khung xương, KHÔNG xử lý URL/Payload nặng"""
        return cls(
            id=str(model.id),
            type=model.type,
            lesson_id=str(getattr(model,'lesson_id',None) or ""),
            title=model.title,
            position=model.position,
            icon_key=cls._map_icon(model.type),
            payload={} # Rỗng để nhẹ
        )

    @classmethod
    def from_model_detail(cls, model):
        """Dùng cho Lesson Detail API: Lấy full, ký tên URL, xử lý HTML"""
        domain = cls.from_model_summary(model) # Tái sử dụng base
        
        # Logic nặng: Ký tên URL, parse HTML...
        domain.payload = cls._process_payload_heavy(model) 
        
        return domain
    
    def to_model(self):
        """
        Chuyển Domain object thành một Model instance (chưa lưu).
        """
        return ContentBlock(
            id=self.id,
            # Service (hàm create_block) sẽ gán lesson (object)
            type=self.type,
            position=self.position,
            payload=self.payload
        )
    
    # # (Hàm apply_updates của bạn có thể giữ nguyên)
    # def apply_updates(self, updates: Dict[str, Any]):
    #     has_payload_update = False
        
    #     for key, value in updates.items():
    #         if hasattr(self, key):
    #             setattr(self, key, value)
    #             if key == 'payload':
    #                 has_payload_update = True

    #     self.validate_basic()
        
    #     if has_payload_update or 'type' in updates:
    #         self.validate_payload()
