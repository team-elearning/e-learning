import uuid
from dataclasses import dataclass
from typing import Dict, Any
from quiz.models import Question 

from media.services.cloud_service import generate_cloudfront_signed_url



@dataclass
class QuestionDomain:
    """
    Đại diện cho domain "Câu hỏi" (Question).
    """
    id: str
    quiz_id: str
    owner_id: uuid.UUID
    owner_name: str
    position: int
    type: str
    prompt: Dict[str, Any]
    answer_payload: Dict[str, Any]
    hint: Dict[str, Any]

    @staticmethod
    def _recursive_sign_urls(data: Any) -> Any:
        """
        Duyệt JSON output (từ DB):
        - Tìm các dict có 'storage_type': 's3_private'.
        - Generate Presigned URL và inject vào field 'url'.
        """
        if isinstance(data, dict):
            # Check nếu dict này là một File Object (do mình quy ước cấu trúc khi lưu)
            if data.get('storage_type') == 's3_private' and 'file_path' in data:
                # Tạo bản sao để không mutate dữ liệu gốc nếu cần dùng lại
                new_file_data = data.copy()
                
                # Generate URL Cloud
                # generate_presigned_url là hàm gọi boto3 generate_presigned_url
                path = f"private/{data['file_path']}"
                
                # UPDATE: Xử lý lỗi nếu gen URL thất bại để không crash API
                try:
                    signed_url = generate_cloudfront_signed_url(path, expiration=3600)
                    new_file_data['url'] = signed_url
                except Exception:
                    new_file_data['url'] = None # Hoặc fallback URL
                
                new_file_data['url'] = signed_url
                return new_file_data

            # Nếu không phải file object, duyệt tiếp các key con
            return {k: QuestionDomain._recursive_sign_urls(v) for k, v in data.items()}

        elif isinstance(data, list):
            return [QuestionDomain._recursive_sign_urls(item) for item in data]

        return data

    @classmethod
    def from_model(cls, model: "Question") -> "QuestionDomain":
        if not model:
            return None
        
        # Lấy raw data từ DB
        raw_prompt = model.prompt or {}
        raw_answer = model.answer_payload or {}
        raw_hint = model.hint or {}

        # ---> BƯỚC QUAN TRỌNG: Inject URL Cloud vào JSON <---
        # Helper này sẽ tìm mọi ngóc ngách có file_path private và thêm field "url": "https://..."
        signed_prompt = QuestionDomain._recursive_sign_urls(raw_prompt)
        signed_answer = QuestionDomain._recursive_sign_urls(raw_answer)
        signed_hint = QuestionDomain._recursive_sign_urls(raw_hint)

        return cls(
            id=str(model.id),
            quiz_id=str(model.quiz_id),
            owner_id=str(model.quiz.owner.id),
            owner_name=str(model.quiz.owner.username),
            position=model.position,
            type=model.type,
            prompt=signed_prompt,       # Data đã có URL
            answer_payload=signed_answer, # Data đã có URL
            hint=signed_hint            # Data đã có URL
        )
    
    def to_dict(self) -> dict:
        """ Chuyển đổi sang dạng dict (JSON-serializable). """
        return self.__dict__