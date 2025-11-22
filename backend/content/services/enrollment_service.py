import uuid
from typing import List
from django.db import transaction
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from custom_account.models import UserModel
from content.domains.enrollment_domain import EnrollmentDomain, EnrollmentCollectionDomain
from core.exceptions import DomainError
from content.models import Course, Enrollment



User = get_user_model()

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


def _ensure_can_manage_course(course_id: uuid.UUID, actor: UserModel) -> None:
    """
    Hàm kiểm tra xem 'actor' có quyền quản lý course_id hay không.
    Quyền quản lý = (Là Admin/Staff) HOẶC (Là Owner).
    """
    # 1. Nếu là Admin/Superuser -> Cho phép (nhưng phải check course tồn tại)
    if actor.is_staff or actor.is_superuser:
        if not Course.objects.filter(id=course_id).exists():
            raise DomainError("Khóa học không tồn tại.")
        return # Pass

    # 2. Nếu là User thường -> Phải là Owner
    is_owner = Course.objects.filter(id=course_id, owner=actor).exists()
    if not is_owner:
        # Báo lỗi chung chung để bảo mật hoặc báo rõ tùy requirement
        raise DomainError("Bạn không có quyền quản lý khóa học này hoặc khóa học không tồn tại.")


def get_course_participants(course_id: uuid.UUID, actor: UserModel) -> List[EnrollmentDomain]:
    """
    Lấy danh sách học viên (Enrollments) của một khóa học.
    Dành cho: Giảng viên (Owner).
    """
    # 1. Check quyền (Dùng helper)
    _ensure_can_manage_course(course_id, actor)

    # 2. Query Enrollment
    # [OPTIMIZATION] Quan trọng: select_related('user') 
    # để lấy luôn info User (tên, avatar, email) trong 1 query duy nhất.
    enrollments = Enrollment.objects.filter(course_id=course_id)\
        .select_related('user')\
        .order_by('-enrolled_at') # Người mới nhất lên đầu

    domain_list = [EnrollmentDomain.from_model(e) for e in enrollments]
    
    return EnrollmentCollectionDomain(
        instance=domain_list,
        total_count=len(domain_list)
    )


def get_participant_detail(course_id: uuid.UUID, target_user_id: uuid.UUID, actor: UserModel) -> Enrollment:
    """
    Lấy thông tin chi tiết 1 học viên cụ thể trong khóa.
    """
    # 1. Check quyền
    _ensure_can_manage_course(course_id, actor)

    # 2. Lấy enrollment
    try:
        enrollment = Enrollment.objects.select_related('user').get(
            course_id=course_id, 
            user_id=target_user_id
        )
        return EnrollmentDomain.from_model(enrollment)
    except Enrollment.DoesNotExist:
        raise DomainError("Học viên này không tồn tại trong khóa học.")


@transaction.atomic
def manual_enroll_user(course_id: uuid.UUID, input: dict, actor: UserModel) -> Enrollment:
    """
    Giảng viên thêm thủ công 1 user vào khóa học.
    """
    target_user_id = input.get('user_id')

    # 1. Validate Course & Quyền Owner
    # Cần load object Course để check logic logic nghiệp vụ khác nếu cần
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        raise DomainError("Khóa học không tồn tại.")

    # 2. Check quyền quản lý trên object vừa lấy
    # (Admin luôn đúng, hoặc Owner ID trùng khớp)
    is_admin = actor.is_staff or actor.is_superuser
    if not is_admin and course.owner_id != actor.id:
        raise DomainError("Bạn không có quyền thêm học viên vào khóa này.")

    # 3. Validate Target User (Không cho add chính Owner vào làm học sinh)
    # (Trừ khi Admin muốn test thì có thể cho phép, nhưng logic này thường chặn)
    if str(course.owner_id) == str(target_user_id):
         raise DomainError("Không thể thêm chính giảng viên làm học viên.")
    
    # Check user tồn tại trong hệ thống không?
    if not User.objects.filter(id=target_user_id).exists():
         raise DomainError("User ID không tồn tại trong hệ thống.")

    # 3. Thực hiện Enroll (Reuse logic hoặc gọi trực tiếp)
    enrollment, created = Enrollment.objects.get_or_create(
        course_id=course_id,
        user_id=target_user_id
    )

    if not created:
        raise DomainError("User này đã là học viên của khóa học rồi.")
    
    return EnrollmentDomain.from_model(enrollment)


def kick_student_from_course(course_id: uuid.UUID, target_user_id: uuid.UUID, actor: UserModel) -> None:
    """
    Giảng viên xóa học viên khỏi khóa học.
    """
    # 1. Check quyền
    _ensure_can_manage_course(course_id, actor)

    # 2. Xóa enrollment
    # Dùng filter().delete() để an toàn và nhanh
    deleted_count, _ = Enrollment.objects.filter(
        course_id=course_id,
        user_id=target_user_id
    ).delete()

    if deleted_count == 0:
        raise DomainError("User này chưa tham gia khóa học hoặc đã bị xóa trước đó.")
    
    return None