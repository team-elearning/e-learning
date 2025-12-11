import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import field


from content.models import Quiz
from quiz.domains.question_domain import QuestionDomain



@dataclass(frozen=True)
class QuizDomain:
    """
    Đại diện cho domain "Bài trắc nghiệm" (Quiz).
    Đây là một DTO (Data Transfer Object) sạch, không phụ thuộc vào Django.
    """
    id: str
    title: str
    time_limit: Optional[timedelta]
    time_open: Optional[datetime]
    time_close: Optional[datetime]
    owner_id: Optional[uuid.UUID]
    owner_name: Optional[str]
    questions: List[QuestionDomain] = field(default_factory=list)
    

    @classmethod
    def from_model(cls, model: "Quiz") -> "QuizDomain":
        """
        Tạo đối tượng QuizDomain từ một instance của Django model Quiz.
        """
        if not model:
            return None
        
        question_domains = [QuestionDomain.from_model(q) for q in model.questions.all()]
        
        return cls(
            id=str(model.id),
            title=model.title,
            time_limit=model.time_limit,
            time_open=model.time_open,
            time_close=model.time_close,
            owner_id=model.owner.id,
            owner_name=model.owner.username,
            questions=question_domains
        )
    
    @classmethod
    def from_model_overview(cls, model: "Quiz") -> "QuizDomain":
        """
        Tạo đối tượng QuizDomain CHỈ chứa metadata (cho List View).
        Hàm này KHÔNG BAO GIỜ chạm vào 'model.questions'.
        """
        if not model:
            return None
        
        return cls(
            id=str(model.id),
            title=model.title,
            time_limit=model.time_limit,
            time_open=model.time_open,
            time_close=model.time_close,
            questions=[] # <-- Luôn trả về list rỗng, không query
        )

    def to_dict(self) -> dict:
        """
        Chuyển đổi đối tượng domain sang dạng dict (JSON-serializable).
        """
        return {
            "id": self.id,
            "title": self.title,
            
            # Chuyển timedelta thành string (ví dụ: '0:45:00')
            "time_limit": str(self.time_limit) if self.time_limit else None,
            
            # Chuyển datetime thành ISO 8601 string (chuẩn cho API)
            "time_open": self.time_open.isoformat() if self.time_open else None,
            "time_close": self.time_close.isoformat() if self.time_close else None,
            "questions": [q.to_dict() for q in self.questions]
        }