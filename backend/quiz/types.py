from typing import List, Optional
from dataclasses import dataclass
from enum import Enum



@dataclass
class ExamFilter:
    """
    Bộ lọc cho Exam. 
    Giúp service linh hoạt, có thể tái sử dụng cho Admin hoặc Student sau này.
    """
    mode: str

    quiz_id: Optional[str] = None
    owner: Optional[object] = None       # Lọc theo người tạo (Giáo viên)
    search_term: Optional[str] = None    # Tìm kiếm theo tiêu đề
    ids: Optional[List[str]] = None      # Lọc theo danh sách ID
    
    # Moodle Style filters:
    is_open: Optional[bool] = None       # True: Đang mở, False: Đã đóng/Chưa mở


class ExamFetchStrategy(Enum):
    """
    Chiến lược lấy dữ liệu.
    """
    LIST_VIEW = "list_view"       # Nhẹ: Chỉ lấy thông tin cơ bản + count số câu hỏi
    DETAIL_VIEW = "detail_view"   # Nặng: Lấy full settings, prefetch câu hỏi
    ANALYTICS = "analytics"       # Thống kê: Kèm theo số lượt làm bài (Attempts)