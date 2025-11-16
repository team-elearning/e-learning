import uuid
from typing import Optional, List, Dict, Any

from content.services.exceptions import DomainValidationError
from content.domains.commands import AddContentBlockCommand
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
            if "image_url" not in self.payload:
                raise DomainValidationError("Payload 'image' phải có 'image_url'.")

        # video
        elif self.type == "video":
            if "video_url" not in self.payload:
                raise DomainValidationError("Payload 'video' phải có 'video_url'.")

        # pdf / docx
        elif self.type in ("pdf", "docx"):
            if "file_url" not in self.payload:
                raise DomainValidationError(f"Payload '{self.type}' phải có 'file_url'.")

        # quiz
        elif self.type == "quiz":
            questions = self.payload.get("questions")
            if not isinstance(questions, list) or len(questions) == 0:
                raise DomainValidationError("Quiz must contain at least one question.")
            
            # Kiểm tra các loại câu hỏi bạn đã định nghĩa trong JSON
            valid_q_types = (
                "multiple_choice_single", "multiple_choice_multi",
                "true_false", "short_answer", "fill_in_the_blank",
                "matching", "essay"
            )
            for idx, q in enumerate(questions):
                if not isinstance(q, dict) or q.get("type") not in valid_q_types:
                    raise DomainValidationError(f"Quiz question[{idx}] invalid or missing type.")
        
        # exploration_ref
        elif self.type == "exploration_ref":
            if "exploration_id" not in self.payload:
                raise DomainValidationError("exploration_ref must include exploration_id.")
        
        # (Không cần else, vì validate_basic đã bắt type không hợp lệ)
        return True

    def to_dict(self):
        return {"id": self.id, "lesson_id": self.lesson_id, "type": self.type, "position": self.position, "payload": self.payload}

    @classmethod
    def from_model(cls, model):
        """
        --- SỬA 3: Lấy 'lesson_id' trực tiếp ---
        (Bỏ hoàn toàn logic 'lesson_version')
        """
        if not model.lesson_id:
            raise ValueError("ContentBlock model is missing lesson_id.")
            
        return cls(
            lesson_id=str(model.lesson_id), # Lấy thẳng ID
            type=model.type, 
            position=model.position, 
            payload=model.payload, 
            id=str(model.id)
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
