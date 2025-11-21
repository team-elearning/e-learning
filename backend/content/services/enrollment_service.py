import uuid
from django.db import transaction
from django.db import IntegrityError

from custom_account.models import UserModel
from content.domains.enrollment_domain import EnrollmentDomain
from core.exceptions import DomainError
from content.models import Course, Enrollment



@transaction.atomic
def enroll_user_in_course(course_id: uuid.UUID, user: UserModel) -> EnrollmentDomain:
    """
    Ghi danh user.
    Refactor: Thêm select_related để tối ưu query nếu cần dùng data course sau này.
    """
    # 1. Tìm khóa học (Kết hợp check published ngay trong query)
    try:
        # select_related 'owner' để tránh thêm query khi check logic bên dưới
        course = Course.objects.select_related('owner').get(id=course_id, published=True)
    except Course.DoesNotExist:
        raise DomainError("Không tìm thấy khóa học hoặc khóa học chưa được xuất bản.")

    # 2. Check quyền: Owner không thể tự enroll
    if course.owner_id == user.id: # So sánh ID nhanh hơn so sánh object
        raise DomainError("Bạn không thể tự ghi danh vào khóa học của chính mình.")

    # 3. Tạo enrollment
    try:
        # get_or_create là chuẩn, giữ nguyên
        enrollment, created = Enrollment.objects.get_or_create(
            user=user,
            course=course
        )
        
        if not created:
            # Nếu đã tồn tại, có thể user đã enroll từ trước
            # (Hoặc logic tái kích hoạt nếu bạn có soft-delete)
            raise DomainError("Bạn đã ghi danh vào khóa học này rồi.")
        
        # TODO: Tại đây nên gọi thêm hàm init_learning_progress(user, course)
        # để tạo sẵn các bản ghi theo dõi tiến độ bài học.
        
        return EnrollmentDomain.from_model(enrollment)
        
    except IntegrityError:
        raise DomainError("Lỗi hệ thống khi ghi danh.")


def unenroll_user_from_course(course_id: uuid.UUID, user: UserModel) -> None:
    """
    Hủy ghi danh.
    Refactor: Dùng filter().delete() để tiết kiệm 1 query SELECT.
    """
    # 1. Xóa trực tiếp (QuerySet Delete)
    # Hàm delete() trả về tuple (số lượng xóa, chi tiết). VD: (1, {'app.Enrollment': 1})
    deleted_count, _ = Enrollment.objects.filter(
        user=user,
        course_id=course_id
    ).delete()

    # 2. Kiểm tra kết quả
    if deleted_count == 0:
        # Nếu = 0 nghĩa là chưa từng enroll -> Báo lỗi nghiệp vụ
        raise DomainError("Bạn chưa ghi danh vào khóa học này hoặc đã hủy trước đó.")
        
    # TODO: Xử lý dọn dẹp tiến độ học tập (Progress) nếu cần
    
    return None