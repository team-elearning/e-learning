from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional, Any
from datetime import datetime, timedelta
import uuid

from quiz.api.dtos.question_dto import QuestionInput, QuestionPublicOutput, QuestionAdminOutput



class ExamCreateInput(BaseModel):
    """
    DTO Input để tạo Exam kèm danh sách câu hỏi.
    """
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None

    # --- Time Config ---
    # Pydantic tự parse chuỗi "00:45:00" thành timedelta
    time_limit: Optional[timedelta] = None 
    time_open: Optional[datetime] = None
    time_close: Optional[datetime] = None

    # --- Rules ---
    max_attempts: Optional[int] = 1
    pass_score: Optional[float] = None
    shuffle_questions: bool = True
    # Exam mặc định ẩn đáp án, nhưng vẫn cho phép override nếu muốn
    show_correct_answer: bool = False 
    
    # Grading method thường là 'first' hoặc 'highest'
    grading_method: str = "first"
    questions_count: int = 10

    # --- Nested Questions ---
    questions: List[QuestionInput] = []

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)


class ExamUpdateInput(BaseModel):
    """
    DTO cho PATCH, mọi trường đều Optional.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    
    time_limit: Optional[timedelta] = None
    time_open: Optional[datetime] = None
    time_close: Optional[datetime] = None
    
    max_attempts: Optional[int] = None
    pass_score: Optional[float] = None
    shuffle_questions: Optional[bool] = None
    questions_count: Optional[int] = None
    
    # List câu hỏi để cập nhật (Create/Update/Delete logic nằm ở Service)
    questions: Optional[List[QuestionInput]] = None


class ExamPublicOutput(BaseModel):
    """
    DTO Output cho Học viên (Xem thông tin bài thi).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str]
    
    # --- Time Infos ---
    time_limit_seconds: Optional[int] = None # Frontend thích giây hơn timedelta object
    time_open: Optional[datetime]
    time_close: Optional[datetime]
    
    # Status label được tính toán từ Domain (upcoming, open, closed)
    status_label: str = "closed" 

    # --- Rules ---
    max_attempts: Optional[int]
    pass_score: Optional[float]
    actual_question_count: int

    # --- Danh sách câu hỏi ---
    # Lưu ý: Thường Exam chưa bắt đầu thì chưa hiện câu hỏi.
    # Nhưng nếu view này dùng để hiển thị "Review" thì dùng QuestionPublicOutput (ẩn đáp án)
    questions: List[QuestionPublicOutput] = []

    @field_validator('questions', mode='before')
    @classmethod
    def convert_manager_to_list(cls, v: Any) -> list:
        if hasattr(v, 'all'):
            return list(v.all())
        if isinstance(v, list):
            return v
        return []
    
    @field_validator('time_limit_seconds', mode='before')
    @classmethod
    def convert_timedelta_to_seconds(cls, v: Any) -> Optional[int]:
        """Helper chuyển DurationField của Django thành số giây (int)"""
        if isinstance(v, timedelta):
            return int(v.total_seconds())
        return v


class ExamAdminOutput(BaseModel):
    """
    DTO Output cho Giáo viên (Soạn thảo & Quản lý).
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str]
    mode: str # Giáo viên cần biết nó là exam hay practice
    
    # --- Time Config Full ---
    time_limit: Optional[timedelta] # Giáo viên cần xem dạng gốc để edit
    time_open: Optional[datetime]
    time_close: Optional[datetime]
    status_label: str = "closed"

    # --- Rules Full ---
    max_attempts: Optional[int]
    pass_score: Optional[float]
    grading_method: str
    shuffle_questions: bool
    show_correct_answer: bool
    
    # --- Stats & Config ---
    config_question_count: int # Số câu cấu hình
    actual_question_count: int = 0 # Số câu thực tế (Từ annotate)

    # --- Questions Full (Kèm đáp án) ---
    questions: List[QuestionAdminOutput] = []

    # --- Validators ---
    @field_validator('questions', mode='before')
    @classmethod
    def convert_manager_to_list(cls, v: Any) -> list:
        if hasattr(v, 'all'):
            return list(v.all()) # QuerySet -> List
        if isinstance(v, list):
            return v
        return []

    def to_dict(self, exclude_none: bool = True) -> dict:
        # Helper convert timedelta thành ISO string khi dump
        data = self.model_dump(exclude_none=exclude_none)
        # Pydantic v2 thường tự handle timedelta thành ISO duration (PnDTnHnMnS)
        # Nếu muốn format khác thì xử lý ở đây
        return data