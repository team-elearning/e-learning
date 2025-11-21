import logging
from typing import List, Dict, Any
from django.db.models import Count, Q
from django.utils import timezone
from django.db import transaction, IntegrityError

from core.exceptions import DomainError
from quiz.types import ExamFilter, ExamFetchStrategy
from quiz.models import Quiz, Question
from quiz.domains.exam_domain import ExamDomain 



logger = logging.getLogger(__name__)

# ==========================================
# INTERNAL HELPERS (Queryset & Mapper)
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


def _bulk_create_questions(quiz, questions_data: List[Dict]):
    """
    Helper: Tạo hàng loạt câu hỏi cho một Quiz.
    Dùng bulk_create để giảm số lượng query xuống Database.
    """
    question_objects = []
    
    for index, q_data in enumerate(questions_data):
        print(f"Processing question {index + 1}:", q_data)
        # Xử lý position: Nếu payload không gửi, tự tăng dần
        position = q_data.get('position', index + 1)
        
        # Tạo instance (chưa save vào DB)
        q_instance = Question(
            quiz=quiz,
            type=q_data.get('type'),
            prompt=q_data.get('prompt', {}),
            answer_payload=q_data.get('answer_payload', {}),
            hint=q_data.get('hint', {}),
            position=position
        )
        question_objects.append(q_instance)
    
    if question_objects:
        try:
            Question.objects.bulk_create(question_objects)
        except Exception as e:
            # Nếu bulk_create lỗi (ví dụ lỗi JSON không hợp lệ), raise lên trên
            raise ValueError(f"Lỗi khi lưu danh sách câu hỏi: {str(e)}")


# ==========================================
# PUBLIC INTERFACE (GET)
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


# ==========================================
# PUBLIC INTERFACE (CREATE)
# ==========================================

@transaction.atomic
def create_exam(user, data: dict, strategy: ExamFetchStrategy = ExamFetchStrategy.DETAIL_VIEW) -> Any:
    """
    Tạo mới Bài thi (Exam).
    
    Logic nghiệp vụ:
    1. Ép buộc mode='exam' (Vì đây là Exam Service).
    2. Validate thời gian (Close > Open).
    3. Tạo Quiz (Cha).
    4. Tạo Questions (Con) - Bulk create để tối ưu.
    5. Trả về Domain.
    """
    
    # 1. Tách dữ liệu lồng nhau (Nested Data)
    # 'questions' là list các dict từ DTO gửi xuống
    questions_data = data.pop('questions', [])
    
    # 2. Thiết lập các giá trị mặc định cho Exam (Moodle Logic)
    data['owner'] = user
    data['mode'] = 'exam' # [IMPORTANT] Luôn force là exam
    
    # Nếu user quên set grading method, Exam thường lấy điểm lần đầu hoặc cao nhất
    if not data.get('grading_method'):
        data['grading_method'] = 'highest'

    # 3. Validate Logic (Business Rules)
    time_open = data.get('time_open')
    time_close = data.get('time_close')
    
    if time_open and time_close and time_open > time_close:
        raise ValueError("Thời gian đóng (Deadline) phải diễn ra SAU thời gian mở.")

    # 4. Tạo Quiz (Core Logic)
    try:
        # Lưu ý: data lúc này chỉ còn các field khớp với Model Quiz
        # Nếu model Quiz của bạn có field 'course', hãy gán: data['course_id'] = course_id
        quiz = Quiz.objects.create(**data)
        
    except IntegrityError as e:
        logger.error(f"Database error creating quiz: {e}")
        raise ValueError("Lỗi dữ liệu khi tạo bài thi (Có thể trùng lặp hoặc lỗi ràng buộc).")
    except Exception as e:
        logger.error(f"Unexpected error creating quiz: {e}")
        raise ValueError(f"Lỗi hệ thống: {str(e)}")

    # 5. Xử lý Questions (Nested Creation)
    if questions_data:
        _bulk_create_questions(quiz, questions_data)

    filters = ExamFilter(ids=[quiz.id], owner=user)
    refreshed_qs = _build_queryset(filters, strategy=ExamFetchStrategy.DETAIL_VIEW)

    try:
        quiz_full = refreshed_qs.get() # Lấy object đã được "bơm" đầy đủ dữ liệu
    except Exception:
        # Fallback nếu query lỗi (hiếm khi xảy ra ngay sau khi create)
        quiz_full = quiz

    # 6. Return Domain
    # Mặc định trả về DETAIL_VIEW để người tạo thấy ngay kết quả (kèm câu hỏi)
    return _map_to_domain(quiz_full, strategy)