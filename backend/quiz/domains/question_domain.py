import uuid
from dataclasses import dataclass
from django.conf import settings
from typing import Dict, Any, Optional


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
    def _recursive_inject_cdn_url(data: Any) -> Any:
        """
        Duyệt JSON output:
        - Tìm object file private.
        - Ghép Clean URL (không query param) để Frontend dùng với Cookie.
        """
        if isinstance(data, dict):
            # Check nếu dict này là một File Object
            if data.get('storage_type') == 's3_private' and 'file_path' in data:
                new_file_data = data.copy()
                
                # --- LOGIC MỚI: CHỈ GHÉP URL SẠCH ---
                # VD: https://cdn.school.com/private/quizzes/abc/xyz.jpg
                cdn_domain = settings.AWS_S3_CUSTOM_DOMAIN
                new_file_data['url'] = f"https://{cdn_domain}/private/{data['file_path']}"
                
                return new_file_data

            # Duyệt tiếp các key con
            return {k: QuestionDomain._recursive_inject_cdn_url(v) for k, v in data.items()}

        elif isinstance(data, list):
            return [QuestionDomain._recursive_inject_cdn_url(item) for item in data]

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
        prompt = QuestionDomain._recursive_inject_cdn_url(raw_prompt)
        answer = QuestionDomain._recursive_inject_cdn_url(raw_answer)
        hint = QuestionDomain._recursive_inject_cdn_url(raw_hint)

        return cls(
            id=str(model.id),
            quiz_id=str(model.quiz_id),
            owner_id=str(model.quiz.owner.id),
            owner_name=str(model.quiz.owner.username),
            position=model.position,
            type=model.type,
            prompt=prompt,       
            answer_payload=answer,
            hint=hint        
        )
    
    def to_dict(self) -> dict:
        """ Chuyển đổi sang dạng dict (JSON-serializable). """
        return self.__dict__
    