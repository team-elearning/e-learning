import uuid
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any

from core.exceptions import DomainValidationError
from content.models import ContentBlock
from media.services.cloud_service import get_signed_url_by_id



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

    @staticmethod
    def _process_payload_heavy(model):
        """
        Logic xử lý nặng:
        1. Ký tên URL cho Video/PDF (Logic cũ).
        2. Parse HTML trong Rich Text để thay thế ID ảnh bằng URL (Logic mới).
        """
        raw_payload = model.payload.copy() if model.payload else {}
        
        try:
            # -------------------------------------------------------
            # CASE 1: RICH TEXT (Soạn thảo như Word)
            # -------------------------------------------------------
            if model.type == 'rich_text':
                html_content = raw_payload.get('html_content', '')
                
                if html_content:
                    # Dùng BeautifulSoup để "mổ xẻ" HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Tìm tất cả thẻ <img> có thuộc tính 'data-id'
                    # (Frontend Editor phải lưu ID vào data-id khi upload)
                    images = soup.find_all('img', attrs={'data-id': True})
                    
                    for img in images:
                        image_id = img['data-id']
                        # Lấy Signed URL (ảnh cache lâu 24h)
                        signed_url = get_signed_url_by_id(image_id, expire_minutes=1440)
                        
                        if signed_url:
                            # Thay thế src="placeholder" thành src="https://cdn..."
                            img['src'] = signed_url
                            
                    # Cập nhật lại HTML đã xử lý vào payload
                    raw_payload['html_content'] = str(soup)

            # -------------------------------------------------------
            # CASE 2: VIDEO (Logic cũ)
            # -------------------------------------------------------
            elif model.type == 'video' and 'video_id' in raw_payload:
                # Video sống 6 tiếng
                url = get_signed_url_by_id(raw_payload['video_id'], expire_minutes=360)
                raw_payload['video_url'] = url

            # -------------------------------------------------------
            # CASE 3: TÀI LIỆU PDF/DOCX (Logic cũ)
            # -------------------------------------------------------
            elif model.type in ('pdf', 'docx') and 'file_id' in raw_payload:
                # Tài liệu sống 2 tiếng
                url = get_signed_url_by_id(raw_payload['file_id'], expire_minutes=120)
                raw_payload['file_url'] = url

            # -------------------------------------------------------
            # CASE 5: QUIZ (Logic cũ)
            # -------------------------------------------------------
            elif model.type == 'quiz':
                if model.quiz_ref_id:
                    raw_payload['quiz_id'] = str(model.quiz_ref_id)

        except Exception as e:
            # Log lỗi nhưng không làm crash app, trả về payload gốc
            print(f"Error processing payload for block {model.id}: {e}")
            pass

        return raw_payload

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
