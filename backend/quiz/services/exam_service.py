import logging
from typing import List
from django.db.models import Count, Q
from django.utils import timezone

from core.exceptions import DomainError
from quiz.types import ExamFilter, ExamFetchStrategy
from quiz.models import Quiz
from quiz.domains.exam_domain import ExamDomain 



logger = logging.getLogger(__name__)

# ==========================================
# 1. INTERNAL HELPERS (Queryset & Mapper)
# ==========================================

def _build_queryset(filters: ExamFilter, strategy: ExamFetchStrategy):
    """
    Hàm nội bộ: Xây dựng QuerySet tối ưu.
    """
    # [MOODLE LOGIC] Quan trọng nhất: Chỉ lấy Quiz có mode là EXAM
    query_set = Quiz.objects.filter(mode='exam')

    # --- A. ÁP DỤNG BỘ LỌC (FILTERS) ---
    if filters.owner:
        query_set = query_set.filter(owner=filters.owner)

    if filters.ids:
        query_set = query_set.filter(id__in=filters.ids)

    if filters.search_term:
        query_set = query_set.filter(title__icontains=filters.search_term)
    
    if filters.course_id:
        # Nếu Quiz có liên kết Course (Optional)
        query_set = query_set.filter(course_id=filters.course_id)

    if filters.is_open is not None:
        now = timezone.now()
        if filters.is_open:
            # Đang mở: (time_open <= now OR null) AND (time_close >= now OR null)
            query_set = query_set.filter(
                (Q(time_open__lte=now) | Q(time_open__isnull=True)) &
                (Q(time_close__gte=now) | Q(time_close__isnull=True))
            )
        else:
            # Đã đóng hoặc chưa mở
            query_set = query_set.filter(
                Q(time_open__gt=now) | Q(time_close__lt=now)
            )

    # --- B. TỐI ƯU HÓA QUERY (STRATEGY) ---
    
    # 1. Chiến lược cho màn hình danh sách (Instructor Dashboard)
    if strategy == ExamFetchStrategy.LIST_VIEW:
        # [MOODLE STYLE]
        # Giáo viên cần biết: "Tôi set random 10 câu, nhưng trong kho thực tế có bao nhiêu câu?"
        # -> Annotate đếm số lượng câu hỏi thực tế đang có trong bank của quiz này.
        query_set = query_set.annotate(
            actual_question_count=Count('questions', distinct=True)
        )
        # Có thể đếm sơ bộ số lượt thi (Attempts) để hiển thị nhanh
        query_set = query_set.annotate(
            attempts_count=Count('attempts', distinct=True)
        )

    # 2. Chiến lược cho màn hình chi tiết / soạn thảo
    elif strategy == ExamFetchStrategy.DETAIL_VIEW:
        # Cần lấy danh sách câu hỏi để hiển thị
        query_set = query_set.prefetch_related('questions')

    # 3. Chiến lược cho thống kê
    elif strategy == ExamFetchStrategy.ANALYTICS:
        # Load kèm các lần làm bài của user để tính điểm trung bình/phổ điểm
        query_set = query_set.prefetch_related('attempts__user')

    # Mặc định sort: Bài mới tạo lên đầu
    return query_set.order_by('-id') # Hoặc created_at nếu có


def _map_to_domain(instance, strategy: ExamFetchStrategy):
    """
    Hàm nội bộ: Chuyển đổi Model -> Domain/DTO.
    """
    if strategy == ExamFetchStrategy.LIST_VIEW:
        # Sử dụng tên hàm mới
        return ExamDomain.from_model_overview(instance)
    
    elif strategy == ExamFetchStrategy.DETAIL_VIEW:
        return ExamDomain.from_model_detail(instance)
    
    # Mặc định fallback
    return ExamDomain.from_model_take_exam(instance)


# ==========================================
# 3. PUBLIC INTERFACE (Service Methods)
# ==========================================

def list_my_exams(user, strategy: ExamFetchStrategy = ExamFetchStrategy.LIST_VIEW) -> List:
    """
    [REQ] Lấy danh sách bài thi do giáo viên này tạo.
    """
    # 1. Tạo Filter context
    filters = ExamFilter(
        owner=user
        # Có thể thêm các logic filter mặc định khác nếu cần
    )

    try:
        # 2. Gọi Internal Builder
        query_set = _build_queryset(filters, strategy)
        
        # 3. Map sang Domain/DTO
        # List comprehension này chạy trên RAM sau khi query execute
        return [_map_to_domain(exam, strategy) for exam in query_set]

    except Exception as e:
        logger.error(f"Error listing my exams for user {user.id}: {e}", exc_info=True)
        # Raise lỗi chung để View bắt và trả về 500
        raise DomainError("Lỗi hệ thống khi lấy danh sách bài thi.")


def get_exam_detail(user, quiz_id: str) -> object:
    """
    Lấy chi tiết 1 bài thi (để Edit settings).
    """
    filters = ExamFilter(owner=user, ids=[quiz_id])
    
    try:
        # Detail cần strategy FULL
        query_set = _build_queryset(filters, strategy=ExamFetchStrategy.DETAIL_VIEW)
        exam = query_set.get() # Raise DoesNotExist nếu ko tìm thấy hoặc sai owner
        return _map_to_domain(exam, ExamFetchStrategy.DETAIL_VIEW)

    except Quiz.DoesNotExist:
        raise DomainError("Không tìm thấy bài thi hoặc bạn không có quyền truy cập.")
    except Exception as e:
        logger.error(f"Error getting exam detail {quiz_id}: {e}", exc_info=True)
        raise DomainError("Lỗi hệ thống.")