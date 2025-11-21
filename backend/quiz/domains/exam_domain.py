import uuid
from datetime import datetime
from typing import List, Optional, Any
from django.utils import timezone

# Giả định bạn đã có QuestionDomain (nếu chưa có thì dùng dict tạm)
# from .question_domain import QuestionDomain 

class ExamDomain:
    """
    Aggregate Root: Exam (Bài thi).
    
    Business Rules:
    - Exam là một tập hợp các Question được cấu hình nghiêm ngặt.
    - Status (Open/Close) được tính toán realtime dựa trên time_open/time_close.
    - Logic validation: Số câu hỏi cấu hình không được vượt quá số câu hỏi thực tế trong kho.
    """

    def __init__(self, 
                 id: str,
                 title: str,
                 mode: str,
                 # Time Config
                 time_limit_seconds: Optional[int] = None, # Convert duration -> seconds
                 time_open: Optional[datetime] = None,
                 time_close: Optional[datetime] = None,
                 status_label: str = "closed", # Calculated: 'upcoming', 'open', 'closed'
                 
                 # Grading Config
                 pass_score: Optional[float] = None,
                 max_attempts: Optional[int] = 1,
                 grading_method: str = "first",
                 shuffle_questions: bool = True,
                 
                 # Question Config
                 config_question_count: int = 0,   # Số câu cài đặt
                 actual_question_count: int = 0,   # Số câu thực tế trong DB (Annotated)
                 questions: List[Any] = None,      # List QuestionDomain objects
                 
                 description: str = "",
                 owner_id: Optional[int] = None,
                 course_id: Optional[str] = None):
        
        self.id = id
        self.title = title
        self.mode = mode
        self.description = description
        self.owner_id = owner_id
        self.course_id = course_id
        
        # Time
        self.time_limit_seconds = time_limit_seconds
        self.time_open = time_open
        self.time_close = time_close
        self.status_label = status_label

        # Config
        self.pass_score = pass_score
        self.max_attempts = max_attempts
        self.grading_method = grading_method
        self.shuffle_questions = shuffle_questions
        
        # Question Data
        self.config_question_count = config_question_count
        self.actual_question_count = actual_question_count
        self.questions = questions or []

    def to_dict(self):
        """Serialize domain to dict for API Response"""
        return {
            "id": self.id,
            "title": self.title,
            "mode": self.mode,
            "description": self.description,
            "owner_id": self.owner_id,
            "course_id": self.course_id,
            
            "time_config": {
                "limit_seconds": self.time_limit_seconds,
                "open": self.time_open,
                "close": self.time_close,
                "status": self.status_label # Frontend dùng cái này để hiển thị badge màu
            },
            "grading_config": {
                "pass_score": self.pass_score,
                "max_attempts": self.max_attempts,
                "grading_method": self.grading_method,
                "shuffle": self.shuffle_questions
            },
            "question_stats": {
                "config_count": self.config_question_count,
                "actual_count": self.actual_question_count,
                "is_shortage": self.actual_question_count < self.config_question_count
            },
            "questions": [q.to_dict() for q in self.questions] if self.questions else []
        }

    # ============================================================
    # BUSINESS LOGIC HELPERS (Moodle Style)
    # ============================================================
    
    @staticmethod
    def _calculate_status(time_open, time_close) -> str:
        """
        Logic xác định trạng thái bài thi.
        """
        now = timezone.now()
        
        if time_open and now < time_open:
            return "upcoming"  # Chưa mở
        
        if time_close and now > time_close:
            return "closed"    # Đã đóng
            
        return "open"          # Đang diễn ra (hoặc luôn mở nếu open/close is None)

    @staticmethod
    def _map_base_attributes(model) -> dict:
        """
        Mapping các trường cơ bản + Tính toán status.
        """
        # 1. Xử lý Time Limit (Duration -> Seconds)
        limit_sec = int(model.time_limit.total_seconds()) if model.time_limit else None
        
        # 2. Tính Status
        status = ExamDomain._calculate_status(model.time_open, model.time_close)
        
        # 3. Lấy actual_question_count từ annotate (nếu Service đã làm)
        # Nếu không có attribute này (do strategy khác), fallback về 0 hoặc query count()
        actual_count = getattr(model, 'actual_question_count', 0)
        if actual_count == 0 and hasattr(model, 'questions'):
             # Fallback nhẹ (chỉ nên dùng khi list ít)
             pass 
             # actual_count = model.questions.count() -> Thường ko nên gọi ở đây để tránh N+1

        return {
            "id": str(model.id),
            "title": model.title,
            "mode": model.mode,
            "description": model.description,
            "owner_id": model.owner_id,
            # Giả sử model Quiz có field course_id
            "course_id": str(model.course_id) if hasattr(model, 'course_id') and model.course_id else None,
            
            "time_limit_seconds": limit_sec,
            "time_open": model.time_open,
            "time_close": model.time_close,
            "status_label": status,
            
            "pass_score": float(model.pass_score) if model.pass_score else None,
            "max_attempts": model.max_attempts,
            "grading_method": model.grading_method,
            "shuffle_questions": model.shuffle_questions,
            
            "config_question_count": model.questions_count,
            "actual_question_count": actual_count,
        }

    # ============================================================
    # FACTORY METHODS
    # ============================================================

    @classmethod
    def from_model_overview(cls, model):
        """
        [STRATEGY: LIST_VIEW]
        Dùng cho danh sách bên ngoài. Nhẹ, không load questions.
        Có thông tin thống kê (actual_question_count) để cảnh báo giáo viên.
        """
        data = cls._map_base_attributes(model)
        # Ở list view, list questions rỗng
        data["questions"] = []
        return cls(**data)

    @classmethod
    def from_model_detail(cls, model):
        """
        [STRATEGY: DETAIL_VIEW]
        Dùng cho màn hình 'Edit Settings' hoặc 'View Detail'.
        Có thể load kèm danh sách câu hỏi (nhưng ở dạng tóm tắt).
        """
        data = cls._map_base_attributes(model)
        
        # Load Questions (Giả định có QuestionDomain)
        # from .question_domain import QuestionDomain
        questions_data = []
        if hasattr(model, 'questions'):
            # Sắp xếp theo position
            qs = model.questions.all().order_by('position')
            for q in qs:
                # questions_data.append(QuestionDomain.from_model_summary(q))
                pass # Tạm thời pass để code chạy đc
                
        data["questions"] = questions_data
        
        return cls(**data)

    @classmethod
    def from_model_take_exam(cls, model):
        """
        [STRATEGY: TAKE_EXAM] - Dành cho sinh viên
        Cực kỳ quan trọng: 
        - Phải ẩn đáp án đúng.
        - Phải xáo trộn câu hỏi (nếu shuffle=True) ngay tại Domain hoặc Service trước khi trả về.
        """
        data = cls._map_base_attributes(model)
        # Logic này sẽ phức tạp hơn, cần xử lý QuestionsOrder
        return cls(**data)