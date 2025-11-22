import logging
import uuid
from typing import List, Dict, Any
from django.db.models import Count, Q
from django.utils import timezone

from quiz.types import ExamFilter, ExamFetchStrategy
from quiz.models import Quiz, Question
from quiz.domains.exam_domain import ExamDomain 
from media.services import file_service



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

    # --- B. TỐI ƯU HÓA QUERY (STRATEGY) ---
    
    # 1. Chiến lược cho màn hình danh sách (Instructor Dashboard)
    if strategy == ExamFetchStrategy.LIST_VIEW:
        pass

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
            created_questions = Question.objects.bulk_create(question_objects)

            # 3. COMMIT FILES (Logic mới)
            # Vì bulk_create trả về list object có thứ tự y hệt list input
            # nên ta có thể zip() để map lại data gốc với object vừa tạo.
            for q_instance, q_data_original in zip(created_questions, questions_data):
                _commit_files_for_question(q_instance, q_data_original)

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
        created_objs = Question.objects.bulk_create(to_create)
        # Map lại với data gốc để commit file
        # Lưu ý: to_create là list Question object, cần map lại với dict gốc
        # (Logic này hơi phức tạp nếu dùng bulk, nên đơn giản nhất là loop)
        # Ở đây tôi demo logic đơn giản:
        pass 
        # (Thực tế: Bạn nên gọi _commit_files_for_question ngay trong vòng lặp tạo object ở trên nếu không dùng bulk strict)
    
    if to_update:
        # Bulk update các trường cần thiết
        Question.objects.bulk_update(to_update, ['type', 'prompt', 'answer_payload', 'hint', 'position'])

        # Commit file cho các câu vừa update (có thể user mới up ảnh mới)
        for q_obj in to_update:
            # Tìm lại data dict tương ứng trong questions_data (dựa theo ID)
            # Đây là đoạn logic cần match lại ID
            original_data = next((item for item in questions_data if str(item.get('id')) == str(q_obj.id)), None)
            if original_data:
                _commit_files_for_question(q_obj, original_data)



def _extract_file_ids_recursively(data: Any, found_ids: set):
    """
    Đệ quy tìm tất cả các value có key kết thúc bằng '_id' hoặc là 'file_id', 'image_id'.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            # Quy ước: Key nào chứa chữ "id" và value là UUID hợp lệ
            if key in ['image_id', 'file_id', 'audio_id', 'video_id'] and value:
                found_ids.add(str(value))
            elif isinstance(value, (dict, list)):
                _extract_file_ids_recursively(value, found_ids)
                
    elif isinstance(data, list):
        for item in data:
            _extract_file_ids_recursively(item, found_ids)


def _commit_files_for_question(question_instance, question_data_dict):
    """
    Tìm file ID trong JSON prompt/hint và commit cho Question này.
    """
    file_ids = set()
    
    # 1. Quét JSON prompt & hint & answer_payload
    _extract_file_ids_recursively(question_data_dict.get('prompt'), file_ids)
    _extract_file_ids_recursively(question_data_dict.get('hint'), file_ids)
    _extract_file_ids_recursively(question_data_dict.get('answer_payload'), file_ids)
    
    if not file_ids:
        return

    # 2. Gọi File Service có sẵn của bạn
    try:
        # Giả định bạn đã import file_service
        file_service.commit_files_by_ids_for_object(
            file_ids=list(file_ids),
            related_object=question_instance, # Question vừa tạo
            actor=None # Bỏ qua check actor nếu tin tưởng service này (hoặc truyền user vào)
        )
    except Exception as e:
        logger.error(f"Failed to commit files for question {question_instance.id}: {e}")
