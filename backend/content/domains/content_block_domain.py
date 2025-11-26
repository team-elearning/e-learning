import uuid
from typing import Optional, List, Dict, Any

from core.exceptions import DomainValidationError
# from content.domains.commands import AddContentBlockCommand
from content.models import ContentBlock



class ContentBlockDomain:
    """
    Domain object cho ContentBlock.
    Đã đồng bộ hóa validation với Serializer.
    """

    # --- SỬA 1: Thêm các type mới ---
    VALID_TYPES = (
        "text", "image", "video", "quiz", 
        "pdf", "docx", "exploration_ref"
    )
    
    # (Bạn có thể giữ lại các hằng số MAX_LENGTH...)

    def __init__(self, lesson_id: str, type: str, position: int = 0, payload: Optional[Dict[str, Any]] = None, id: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.lesson_id = lesson_id
        self.type = type
        self.position = int(position)
        self.payload = payload or {}
        
        # Chạy validate
        self.validate_basic()
        self.validate_payload() # Nên validate cả payload khi khởi tạo

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

    @classmethod
    def from_model(cls, model):
        """
        Khởi tạo Domain object từ Model.
        Xử lý và "làm giàu" payload ngay tại thời điểm này.
        """
        if not model.lesson_id:
            raise ValueError("ContentBlock model is missing lesson_id.")
        
        # 1. Lấy payload thô từ CSDL
        raw_payload = model.payload
        
        # 2. Tạo một bản sao để "làm giàu"
        #    (Không làm thay đổi payload gốc của model)
        processed_payload = raw_payload.copy()
        
        # 3. Xử lý payload DỰA TRÊN TYPE
        try:
            if model.type == 'image' and 'image_id' in raw_payload:
                image_id = raw_payload['image_id']
                if image_id:
                    processed_payload['image_url'] = f"/api/media/files/{image_id}/"
            
            elif model.type in ('pdf', 'docx') and 'file_id' in raw_payload:
                file_id = raw_payload['file_id']
                if file_id:
                    processed_payload['file_url'] = f"/api/media/files/{file_id}/"
    
            elif model.type == 'video' and 'video_id' in raw_payload:
                video_id = raw_payload['video_id']
                if video_id:
                    processed_payload['video_url'] = f"/api/media/files/{video_id}/"
            
            elif model.type == 'quiz':
                # Lấy ID từ trường tham chiếu (ForeignKey)
                if model.quiz_ref_id:
                    if not getattr(model, 'quiz_ref_id', None):
                        # Chủ động ném lỗi để nhảy xuống except Exception bên dưới
                        raise ValueError(f"Quiz Block ID {model.id} missing 'quiz_ref_id'")
                
                processed_payload['quiz_id'] = str(model.quiz_ref_id)
            
        except KeyError:
            # Bỏ qua nếu cấu trúc payload bị sai
            pass 
        except Exception:
            # Bỏ qua nếu có lỗi, giữ payload gốc
            processed_payload = raw_payload

        # 4. Khởi tạo class với payload đã được xử lý
        return cls(
            lesson_id=str(model.lesson_id),
            type=model.type, 
            position=model.position, 
            payload=processed_payload, # <-- Dùng payload đã xử lý
            id=str(model.id),
        )
    
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
    
    # (Hàm apply_updates của bạn có thể giữ nguyên)
    def apply_updates(self, updates: Dict[str, Any]):
        has_payload_update = False
        
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
                if key == 'payload':
                    has_payload_update = True

        self.validate_basic()
        
        if has_payload_update or 'type' in updates:
            self.validate_payload()
