import logging
from typing import List, Any
from django.db import transaction

from custom_account.models import UserModel
from core.exceptions import DomainError
from quiz.types import ExamFilter, ExamFetchStrategy
from quiz.models import Quiz
from quiz.services.base_service import _build_queryset, _map_to_domain, _bulk_create_questions, _process_nested_questions



logger = logging.getLogger(__name__)

# ==========================================
# PUBLIC INTERFACE (GET)
# ==========================================

def list_quizzes(filters: ExamFilter, strategy: ExamFetchStrategy.LIST_VIEW) -> List:
    """ Lấy danh sách Quiz (Exam/Practice) """

    try:
        query_set = _build_queryset(filters, strategy)
        return [_map_to_domain(q, strategy) for q in query_set]
    except Exception as e:
        logger.error(f"Error listing quizzes: {e}", exc_info=True)
        raise DomainError(f"Lỗi hệ thống khi lấy danh sách bài tập - {str(e)}")


def get_quiz_single(filters: ExamFilter, strategy: ExamFetchStrategy = ExamFetchStrategy.DETAIL_VIEW) -> Any:
    """ Lấy chi tiết 1 Quiz """
    try:
        query_set = _build_queryset(filters, strategy)
        quiz = query_set.get()
        return _map_to_domain(quiz, strategy)
    except Quiz.DoesNotExist:
        raise DomainError("Không tìm thấy bài tập hoặc bạn không có quyền truy cập.")
    except Exception as e:
        logger.error(f"Error getting quiz detail: {e}", exc_info=True)
        raise DomainError("Lỗi hệ thống.")


# ==========================================
# PUBLIC INTERFACE (CREATE)
# ==========================================

@transaction.atomic
def create_quiz(
    data: dict, 
    created_by: UserModel, 
    mode: str, # Bắt buộc truyền 'exam' hoặc 'practice'
    output_strategy: ExamFetchStrategy = ExamFetchStrategy.DETAIL_VIEW
) -> Any:
    """
    Hàm nội bộ: Tạo Quiz chung cho mọi chế độ.
    Args:
        mode: 'exam' hoặc 'practice' (để set cứng)
        defaults: Các setting mặc định (ví dụ grading_method)
    """
    questions_data = data.pop('questions', [])
    
    # 2. Xử lý Owner (Admin có thể tạo hộ)
    owner = data.get('owner', created_by)

    # 1. Apply Defaults & Force Mode
    data['owner'] = owner
    data['mode'] = mode 

    # Default grading method nếu thiếu
    if not data.get('grading_method'):
        data['grading_method'] = 'highest' if mode == 'exam' else 'highest'
    
    # 2. Validate Time (Chung)
    time_open = data.get('time_open')
    time_close = data.get('time_close')
    if time_open and time_close and time_open > time_close:
        raise ValueError("Thời gian đóng phải diễn ra SAU thời gian mở.")

    # 3. Create Quiz
    try:
        quiz = Quiz.objects.create(**data)
    except Exception as e:
        logger.error(f"Error creating quiz: {e}")
        raise ValueError(f"Lỗi hệ thống: {str(e)}")

    # 4. Create Questions
    if questions_data:
        _bulk_create_questions(quiz, questions_data) 

    # 7. Refetch & Return
    # Tái sử dụng hàm get_quiz_single để lấy full data vừa tạo
    return get_quiz_single(
        filters=ExamFilter(quiz_id=quiz.id, mode=mode, owner=owner), 
        strategy=output_strategy
    )


# ==========================================
# PUBLIC INTERFACE (PATCH)
# ==========================================

@transaction.atomic
def patch_quiz(
    quiz_id: str, 
    data: dict, 
    actor: UserModel, 
    target_mode: str,
    output_strategy: ExamFetchStrategy = ExamFetchStrategy.DETAIL_VIEW
) -> Any:
    """
    Hàm nội bộ: Update Quiz.
    Args:
        target_mode: Để đảm bảo API Exam không sửa nhầm bài Practice.
    """

    # 1. Check quyền & Lấy object gốc
    try:
        is_admin = getattr(actor, 'is_staff', False) or getattr(actor, 'is_superuser', False)
        
        qs = Quiz.objects.filter(mode=target_mode) # Luôn lock mode để an toàn
        
        if is_admin:
            quiz = qs.get(id=quiz_id) # Admin sửa của ai cũng được
        else:
            quiz = qs.get(id=quiz_id, owner=actor) # Instructor chỉ sửa của mình
            
    except Quiz.DoesNotExist:
        raise ValueError("Không tìm thấy bài tập hoặc bạn không có quyền chỉnh sửa.")

    # 2. Tách Nested Data
    questions_data = data.pop('questions', None)

    # Validate Time
    new_open = data.get('time_open', quiz.time_open)
    new_close = data.get('time_close', quiz.time_close)
    if new_open and new_close and new_open > new_close:
        raise ValueError("Thời gian đóng phải diễn ra SAU thời gian mở.")

    # Prevent Mode Change
    if 'mode' in data and data['mode'] != target_mode:
        raise ValueError(f"Không được phép chuyển đổi bài này sang chế độ khác.")

    # Update Fields
    for field, value in data.items():
        if hasattr(quiz, field):
            setattr(quiz, field, value)
    quiz.save()

    # Diff Questions
    if questions_data is not None:
        _process_nested_questions(quiz, questions_data) # Hàm Diff Engine giữ nguyên

    # 7. Return
    return get_quiz_single(
        filters=ExamFilter(quiz_id=quiz.id, mode=target_mode), 
        strategy=output_strategy
    )


# ==========================================
# PUBLIC INTERFACE (DELETE)
# ==========================================

def delete_quiz(quiz_id: str, actor: UserModel, target_mode: str) -> None:
    try:
        is_admin = getattr(actor, 'is_staff', False) or getattr(actor, 'is_superuser', False)
        
        qs = Quiz.objects.filter(mode=target_mode)
        
        if is_admin:
            quiz = qs.get(id=quiz_id)
        else:
            quiz = qs.get(id=quiz_id, owner=actor)
            
    except Quiz.DoesNotExist:
        raise ValueError("Không tìm thấy bài tập hoặc bạn không có quyền xóa.")

    if quiz.attempts.exists():
        raise ValueError("KHÔNG THỂ XÓA: Đã có học viên làm bài. Vui lòng ẩn bài thi đi.")
    
    quiz.delete()