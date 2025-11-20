from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
import uuid

from custom_account.models import UserModel



# 1. Enum Chiến lược: Quyết định độ sâu dữ liệu
class CourseFetchStrategy(str, Enum):
    OVERVIEW = 'overview'           # Nhẹ nhất: Cho danh sách
    FULL_STRUCTURE = 'full_struct'  # Vừa phải: Cho màn hình học/sửa nội dung
    ADMIN_DETAIL = 'admin_detail'   # Nặng nhất: Cho Admin soi chi tiết User/Subject


# 2. Dataclass Bộ lọc: Quyết định lấy bản ghi nào
@dataclass
class CourseFilter:
    course_id: Optional[uuid.UUID] = None       # Lấy 1 cái cụ thể
    ids: Optional[List[uuid.UUID]] = None       # Lấy 1 danh sách ID cụ thể
    owner: Optional[UserModel] = None           # Lấy của ai tạo
    enrolled_user: Optional[UserModel] = None   # Lấy khóa user này đã mua/enroll
    published_only: bool = False                # Chỉ lấy public
    search_term: Optional[str] = None           # Tìm kiếm