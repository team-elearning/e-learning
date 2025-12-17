from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List
import uuid

from custom_account.models import UserModel



# 1. Enum Chiến lược: Quyết định độ sâu dữ liệu
class CourseFetchStrategy(str, Enum):
    # 0. Cơ bản
    BASIC = auto()

    # 1. Màn hình danh sách (User/Guest) - Nhẹ nhất
    CATALOG_LIST = auto()
    
    MY_ENROLLED = auto()
    
    # 2. Cấu trúc khóa học (User/Guest) - Xem trước nội dung
    STRUCTURE = auto()

    # 3. Dashboard giáo viên
    INSTRUCTOR_DASHBOARD = auto()

    INSTRUCTOR_DETAIL = auto()
    
    # 3. Màn hình quản lý danh sách (Admin) - Cần sort/filter, stats hệ thống
    ADMIN_LIST = auto()
    
    # 4. Màn hình chi tiết quản lý (Admin) - Full tất cả để debug/audit
    ADMIN_DETAIL = auto()


# 2. Dataclass Bộ lọc: Quyết định lấy bản ghi nào
@dataclass
class CourseFilter:
    course_id: Optional[uuid.UUID] = None       # Lấy 1 cái cụ thể
    ids: Optional[List[uuid.UUID]] = None       # Lấy 1 danh sách ID cụ thể
    owner: Optional[UserModel] = None           # Lấy của ai tạo
    enrolled_user: Optional[UserModel] = None   # Lấy khóa user này đã mua/enroll
    exclude_enrolled_user: Optional[UserModel] = None  # Dùng để loại trừ khóa "Của tôi" ra khỏi list public
    published_only: bool = False                # Chỉ lấy public
    search_term: Optional[str] = None           # Tìm kiếm