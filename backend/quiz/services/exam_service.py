import logging
import uuid
from typing import List, Dict, Any
from django.db.models import Count, Q
from django.utils import timezone
from django.db import transaction

from custom_account.models import UserModel
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
    # 1. Filter bắt buộc theo Mode
    query_set = Quiz.objects.filter(mode=filters.mode)

    # --- A. ÁP DỤNG BỘ LỌC (FILTERS) ---
    if filters.quiz_id:
        query_set = query_set.filter(id=filters.quiz_id)

    if filters.owner:
        query_set = query_set.filter(owner=filters.owner)

    if filters.ids:
        query_set = query_set.filter(id__in=filters.ids)

    if filters.search_term:
        query_set = query_set.filter(title__icontains=filters.search_term)

    # Logic lọc thời gian (Is Open)
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
        query_set = query_set.select_related('owner').prefetch_related('attempts__user')

    # Mặc định sort: Bài mới tạo lên đầu
    return query_set.order_by('-created_at') # Hoặc created_at nếu có


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
        
    
def _process_nested_questions(quiz, questions_data: list):
    """
    Helper: Diff Engine xử lý danh sách câu hỏi.
    Logic: Full Sync (Đồng bộ hoàn toàn theo list mới gửi lên).
    """
    # A. Danh sách ID các câu hỏi ĐANG CÓ trong DB
    existing_ids = set(quiz.questions.values_list('id', flat=True))
    
    # B. Danh sách ID các câu hỏi ĐƯỢC GỬI LÊN
    incoming_ids = set()
    for q in questions_data:
        q_id = q.get('id')
        if q_id:
            incoming_ids.add(uuid.UUID(str(q_id))) # Convert str -> UUID để so sánh

    # --- ACTION 1: DELETE (Có trong DB nhưng không có trong List gửi lên) ---
    to_delete_ids = existing_ids - incoming_ids
    if to_delete_ids:
        # [MOODLE LOGIC] Check xem câu hỏi này đã có ai làm bài chưa?
        # Nếu chưa -> Xóa cứng. Nếu rồi -> Có thể chặn hoặc Soft Delete (Ở đây ta xóa cứng cho đơn giản)
        Question.objects.filter(id__in=to_delete_ids).delete()

    # --- ACTION 2 & 3: CREATE & UPDATE ---
    to_create = []
    to_update = []

    for index, q_data in enumerate(questions_data):
        # Tự động đánh lại số thứ tự (Position) theo thứ tự mảng
        q_data['position'] = index + 1
        
        q_id = q_data.get('id')
        
        if q_id:
            # --- UPDATE ---
            # Tìm object trong DB (để đảm bảo nó thuộc quiz này)
            # Lưu ý: Không query DB trong vòng lặp. Ta sẽ dùng bulk_update.
            # Ở đây tôi dùng update từng cái cho an toàn logic JSONField, 
            # nhưng tối ưu hơn là dùng bulk_update.
            try:
                q_obj = Question.objects.get(id=q_id, quiz=quiz)
                q_obj.type = q_data.get('type', q_obj.type)
                q_obj.prompt = q_data.get('prompt', q_obj.prompt)
                q_obj.answer_payload = q_data.get('answer_payload', q_obj.answer_payload)
                q_obj.hint = q_data.get('hint', q_obj.hint)
                q_obj.position = q_data['position']
                to_update.append(q_obj)
            except Question.DoesNotExist:
                # ID gửi lên nhưng không tìm thấy -> Bỏ qua hoặc báo lỗi
                continue
        else:
            # --- CREATE ---
            to_create.append(Question(
                quiz=quiz,
                type=q_data.get('type'),
                prompt=q_data.get('prompt', {}),
                answer_payload=q_data.get('answer_payload', {}),
                hint=q_data.get('hint', {}),
                position=q_data['position']
            ))

    # Thực thi DB
    if to_create:
        Question.objects.bulk_create(to_create)
    
    if to_update:
        # Bulk update các trường cần thiết
        Question.objects.bulk_update(to_update, ['type', 'prompt', 'answer_payload', 'hint', 'position'])


# def _refetch_quiz_domain(quiz_id, user) -> Any:
#     """
#     Hàm Helper: 
#     Query lại Quiz từ DB với đầy đủ dữ liệu (Questions, Annotations) 
#     sau khi vừa Create hoặc Update xong.
#     """
#     # 1. Tạo bộ lọc theo ID vừa xử lý
#     filters = ExamFilter(ids=[quiz_id], owner=user)
    
#     # 2. Dùng Strategy DETAIL_VIEW để lấy:
#     # - Danh sách câu hỏi (prefetch_related)
#     # - Số lượng thực tế (actual_question_count từ annotate)
#     refreshed_qs = _build_queryset(filters, strategy=ExamFetchStrategy.DETAIL_VIEW)
    
#     try:
#         # Lấy object đã được "bơm" đầy đủ dữ liệu từ DB
#         quiz_full = refreshed_qs.get() 
#     except Exception:
#         # Fallback hiếm gặp: Nếu query phức tạp lỗi thì lấy object thường
#         # (Để tránh crash API, dù data có thể thiếu chút ít)
#         quiz_full = Quiz.objects.get(id=quiz_id)

#     # 3. Map sang Domain
#     return _map_to_domain(quiz_full, strategy=ExamFetchStrategy.DETAIL_VIEW)


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
        raise DomainError("Lỗi hệ thống khi lấy danh sách bài tập.")


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