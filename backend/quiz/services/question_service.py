import logging
import uuid
from typing import Dict, Any, List
from django.db import transaction
from django.conf import settings
from django.db.models import Max

from quiz.domains.question_domain import QuestionDomain
from core.exceptions import DomainError
from media.services.cloud_service import s3_copy_object
from media.models import UploadedFile, FileStatus
from quiz.models import Quiz, Question



UserModel = settings.AUTH_USER_MODEL

logger = logging.getLogger(__name__)


# ==========================================
# PUBLIC INTERFACE (HELPERS)
# ==========================================

def _extract_file_ids_from_json(data: Any) -> List[str]:
    """Tìm tất cả value có key là 'image_id' hoặc 'file_id' trong JSON"""
    ids = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ['image_id', 'file_id', 'video_id', 'audio_id'] and value:
                ids.append(value)
            else:
                ids.extend(_extract_file_ids_from_json(value))
    elif isinstance(data, list):
        for item in data:
            ids.extend(_extract_file_ids_from_json(item))
    return ids


def _promote_single_file(staging_id: str, question: Question) -> dict | None:
    """
    Input: UUID của file Staging.
    Output: Dict chứa path mới và metadata (để replace vào JSON cũ).
    """
    try:
        # 1. Tìm file trong bảng tạm
        uploaded_file = UploadedFile.objects.get(id=staging_id, status=FileStatus.STAGING)
        
        # 2. Tạo đường dẫn "Sạch" cho Question
        # Cấu trúc: courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}/{uuid}.ext
        ext = uploaded_file.file.name.split('.')[-1]
        
        relative_path = f"quizzes/{question.quiz_id}/questions/{question.id}/{uuid.uuid4()}.{ext}"
        
        s3_src_key = uploaded_file.file.name
        s3_dest_key = f"private/{relative_path}" # Prefix 'private/'

        # 3. Move trên S3
        s3_copy_object(s3_src_key, s3_dest_key, is_public=False)

        # 4. Trả về data mới để update vào JSON
        meta = {
            "file_path": relative_path,
            "storage_type": "s3_private",
            "file_name": uploaded_file.original_filename,
            "file_size": uploaded_file.file_size,
            "mime_type": uploaded_file.mime_type,
        }
        
        # 5. Dọn dẹp DB
        uploaded_file.delete()

        return meta

    except UploadedFile.DoesNotExist:
        logger.warning(f"Staging file {staging_id} not found or already processed.")
        return None
    except Exception as e:
        logger.error(f"Error promoting question file: {e}")
        return None
    

def _recursive_process_json(data: Any, question: Question) -> Any:
    """
    Duyệt JSON input:
    - Tìm key kết thúc bằng '_staging_id'.
    - Promote file lên S3 Private.
    - Trả về data mới đã thay thế '_staging_id' bằng '_data' (chứa file_path).
    """
    if isinstance(data, dict):
        # 1. Tạo bản sao để xử lý (tránh sửa trực tiếp input và dễ return)
        new_data = data.copy()

        # 2. Xử lý Logic File (Promote Staging -> Private)
        # Check ngay trên level object này xem có phải là File Object không
        if 'file_id' in new_data and not new_data.get('file_path'):
            staging_id = new_data['file_id']
            
            # Gọi hàm promote
            file_info = _promote_single_file(staging_id, question)
            
            if file_info:
                new_data.update(file_info)
                # Tùy chọn: Xóa file_id thừa đi cho sạch
                # if 'file_id' in new_data: del new_data['file_id']
            else:
                new_data['error'] = "File not found or processing failed"

        # 3. Đệ quy tiếp cho các key con (để xử lý nested structures)
        # Ví dụ: prompt -> media (list) -> item (dict) -> file_id
        for key, value in new_data.items():
            if isinstance(value, (dict, list)):
                new_data[key] = _recursive_process_json(value, question)

        return new_data

    elif isinstance(data, list):
        # Nếu là List (ví dụ danh sách đáp án), duyệt từng phần tử
        return [_recursive_process_json(item, question) for item in data]

    # Giá trị cơ bản (str, int, bool) -> Giữ nguyên
    return data


# ==========================================
# PUBLIC INTERFACE (CREATE)
# ==========================================

@transaction.atomic
def create_question(quiz_id: uuid.UUID, data: Dict[str, Any]) -> QuestionDomain:
    """
    Tạo câu hỏi rỗng (Skeleton).
    Nếu data không có 'type', mặc định là 'multiple_choice'.
    """
    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        raise ValueError("Quiz không tồn tại.")

    # 1. Tự động tính Position (Append vào cuối danh sách)
    max_pos = Question.objects.filter(quiz=quiz).aggregate(Max('position'))['position__max']
    new_position = 1 if max_pos is None else max_pos + 1

    # 2. Lấy type (Mặc định nếu thiếu)
    # Bạn có thể define hằng số DEFAULT_QUESTION_TYPE = 'multiple_choice'
    q_type = data.get('type', 'multiple_choice')

    # 3. Tạo Question với payload rỗng
    new_q = Question.objects.create(
        quiz=quiz,
        position=new_position,
        type=q_type,     # Type đã xử lý default
        prompt={},       # Luôn rỗng khi mới tạo
        answer_payload={},
        hint={}
    )
    
    return QuestionDomain.from_model(new_q)


# ==========================================
# PUBLIC INTERFACE (UPDATE)
# ==========================================

@transaction.atomic
def update_question(question_id: uuid.UUID, data: Dict[str, Any]) -> QuestionDomain:
    """
    Cập nhật Question.
    Hỗ trợ:
    1. Cập nhật field thường (type, position).
    2. Cập nhật JSON (prompt, answer, hint) VÀ tự động quét file mới để promote lên S3 Private.
    """
    try:
        q_to_update = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        raise DomainError(f"Question {question_id} không tìm thấy để cập nhật.")

    # 1. Validate Type: CẤM ĐỔI TYPE
    if 'type' in data:
        requested_type = data['type']
        current_type = q_to_update.type
        
        # Nếu gửi type khác type hiện tại -> Chặn luôn
        if requested_type != current_type:
            raise DomainError(
                f"Không được phép thay đổi loại câu hỏi. "
                f"Hiện tại: '{current_type}', Yêu cầu: '{requested_type}'. "
                f"Hãy xóa và tạo mới nếu muốn đổi loại."
            )
        
        # Nếu type giống nhau thì không cần làm gì cả (pass), 
        # vì type không được phép thay đổi.

    if 'score' in data:
        q_to_update.score = data['score']

    # 2. Update JSON fields với logic quét File (Recursive Scan)
    
    # --- Xử lý Prompt ---
    if 'prompt' in data: 
        # Frontend gửi toàn bộ nội dung mới của prompt.
        # Hàm quét sẽ tìm các key '_staging_id' mới để xử lý.
        # Các key cũ (đã là '_data') sẽ được giữ nguyên.
        q_to_update.prompt = _recursive_process_json(data['prompt'], q_to_update)

    # --- Xử lý Answer Payload ---
    if 'answer_payload' in data: 
        q_to_update.answer_payload = _recursive_process_json(data['answer_payload'], q_to_update)

    # --- Xử lý Hint ---
    if 'hint' in data: 
        q_to_update.hint = _recursive_process_json(data['hint'], q_to_update)
    
    # 3. Save
    q_to_update.save()
    
    return QuestionDomain.from_model(q_to_update)


# ==========================================
# PUBLIC INTERFACE (DELETE)
# ==========================================

@transaction.atomic
def delete_question(question_id: uuid.UUID):
    """
    Xóa MỘT Question.
    """
    try:
        q_to_delete = Question.objects.get(id=question_id)
        q_to_delete.delete()
    except Question.DoesNotExist:
        # Bỏ qua nếu câu hỏi đã bị xóa
        pass
    return


# ==========================================
# PUBLIC INTERFACE (GET)
# ==========================================

def list_questions_for_quiz(quiz_id: uuid.UUID) -> List[QuestionDomain]:
    """
    Lấy danh sách các Question (dưới dạng Domain) cho 1 Quiz.
    """
    questions = Question.objects.filter(quiz_id=quiz_id).order_by('position')
    return [QuestionDomain.from_model(q) for q in questions]


def get_question_detail(question_id: uuid.UUID) -> QuestionDomain:
    """
    Lấy chi tiết một Question theo ID.
    """
    try:
        # select_related 'quiz' để tối ưu nếu cần truy xuất thông tin quiz cha
        question = Question.objects.select_related('quiz').get(id=question_id)
        return QuestionDomain.from_model(question)
    except Question.DoesNotExist:
        raise ValueError(f"Question với ID {question_id} không tồn tại.")