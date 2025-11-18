# --- File mới: quiz_service.py ---
import uuid
from typing import Dict, Any, Tuple, List
from django.db import transaction
from datetime import timedelta

from content.models import Quiz, Question
from content.domains.quiz_domain import QuizDomain

from typing import Dict, Any, Tuple, List, Optional
from datetime import timedelta
from django.db import transaction
from django.db.models import Prefetch

# (Giả sử) UserModel của bạn
from django.conf import settings
UserModel = settings.AUTH_USER_MODEL

from content.models import Quiz, Question
from content.domains.quiz_domain import QuizDomain
from content.services.exceptions import DomainError
from content.services import question_service



@transaction.atomic
def create_quiz(data: Dict[str, Any]) -> QuizDomain:
    """
    Tạo Quiz và các Question con từ DTO.
    """
    questions_data = data.pop('questions', [])

    # 1. Tạo Quiz (object gốc)
    new_quiz = Quiz.objects.create(
        title=data.get('title', 'Bài tập không tiêu đề'),
        time_limit=data.get('time_limit'),
        time_open=data.get('time_open'),
        time_close=data.get('time_close')
    )
    
    # 2. Tạo Questions (con)
    for question_data in questions_data:
        question_service.create_question(quiz=new_quiz, data=question_data)

    quiz_with_questions = Quiz.objects.prefetch_related('questions').get(id=new_quiz.id)
    return QuizDomain.from_model(quiz_with_questions)


@transaction.atomic
def patch_quiz(quiz_id: uuid.UUID, data: Dict[str, Any], user: UserModel) -> QuizDomain:
    """
    Cập nhật (PATCH) Quiz và các Question con theo logic "Moodle" (C/U/D).
    """
    
    # 1. Lấy Quiz gốc
    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        raise ValueError("Quiz not found.")

    # Check quyền: User phải là admin/staff hoặc là chủ của khóa học
    block = quiz.content_blocks.first() # Lấy block đang dùng quiz này
    if not block:
        raise DomainError("Không thể sửa Quiz mồ côi (không thuộc bài học nào).")
    
    course_owner = block.lesson.module.course.owner
    if not (user.is_superuser or user.is_staff or course_owner == user):
        raise DomainError("Bạn không có quyền chỉnh sửa quiz này.")
    
    questions_data = data.get('questions', None)

    # 2. Cập nhật trường đơn giản của Quiz (title, time_limit...)
    simple_fields = ['title', 'time_limit', 'time_open', 'time_close']
    fields_to_update = []
    for field in simple_fields:
        if field in data:
            value = data[field]
            
            setattr(quiz, field, value)
            fields_to_update.append(field)
    
    if fields_to_update:
        quiz.save(update_fields=fields_to_update)

    # 3. Xử lý 'questions' (LOGIC MOODLE ĐÃ REFACTOR)
    if questions_data is not None:
        
        existing_question_ids = set(quiz.questions.values_list('id', flat=True))
        incoming_question_ids = set()

        for position, question_data in enumerate(questions_data):
            question_data['position'] = position # Gán lại vị trí
            question_id_str = question_data.get('id')
            
            if question_id_str:
                # --- UPDATE (U) ---
                question_id = uuid.UUID(str(question_id_str))
                if question_id not in existing_question_ids:
                    raise DomainError(f"Question {question_data.get('prompt')} không thuộc quiz này.")
                
                # Ủy quyền cho question_service
                question_service.patch_question(question_id=question_id, data=question_data)
                
                incoming_question_ids.add(question_id)
            else:
                # --- CREATE (C) ---
                # Ủy quyền cho question_service
                new_question_domain = question_service.create_question(quiz=quiz, data=question_data)
                incoming_question_ids.add(uuid.UUID(new_question_domain.id))

        # --- DELETE (D) ---
        ids_to_delete = existing_question_ids - incoming_question_ids
        for question_id in ids_to_delete:
            # Ủy quyền cho question_service
            question_service.delete_question(question_id=question_id)
            
    # 4. Lấy lại Quiz đã cập nhật (bao gồm questions) để trả về
    quiz_updated = Quiz.objects.prefetch_related('questions').get(id=quiz_id)
    return QuizDomain.from_model(quiz_updated)


def get_quiz_details(quiz_id: uuid.UUID, user: UserModel) -> QuizDomain:
    """
    Lấy chi tiết 1 Quiz (lồng cả questions) và check quyền.
    """
    try:
        # Tải sẵn 'questions' để QuizDomain.from_model có thể dùng
        quiz = Quiz.objects.prefetch_related('questions').get(id=quiz_id)
    except Quiz.DoesNotExist:
        raise DomainError("Bài quiz không tìm thấy.")
        
    # (Logic check quyền của bạn giữ nguyên)
    block = quiz.content_blocks.first()
    if not block:
        raise DomainError("Không thể truy cập Quiz mồ côi (không thuộc bài học nào).")
    course_owner = block.lesson.module.course.owner
    if not (user.is_superuser or user.is_staff or course_owner == user):
        raise DomainError("Bạn không có quyền xem quiz này.")
        
    # from_model giờ đã tự động lồng 'questions'
    return QuizDomain.from_model(quiz)


def list_all_quizzes() -> List[QuizDomain]:
    """
    Lấy list TOÀN BỘ quiz (dành cho Admin).
    """
    # LƯU Ý: Không prefetch 'questions' ở đây
    # vì đây là list view, không cần chi tiết câu hỏi
    quizzes = Quiz.objects.all().order_by('title')
    
    # QuizDomain.from_model sẽ chạy và trả về
    # 'questions=[]' (rỗng) cho mỗi quiz, rất hiệu quả
    return [QuizDomain.from_model_overview(q) for q in quizzes]


@transaction.atomic
def delete_quiz(quiz_id: uuid.UUID, user: UserModel):
    """
    Xóa một Quiz VÀ check logic nghiệp vụ.
    """
    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        raise DomainError("Quiz không tìm thấy.")

    # Check quyền
    block = quiz.content_blocks.first()
    course_owner = None
    if block:
        course_owner = block.lesson.module.course.owner
    
    # Chỉ Superuser HOẶC chủ sở hữu (nếu quiz có chủ) mới được xóa
    if not (user.is_superuser or (course_owner and course_owner == user)):
        raise DomainError("Bạn không có quyền xóa quiz này.")

    # --- CHECK LOGIC NGHIỆP VỤ QUAN TRỌNG ---
    # Không thể xóa Quiz nếu nó đang được sử dụng
    if block:
        raise DomainError(
            f"Không thể xóa. Quiz đang được sử dụng trong bài học: "
            f"'{block.lesson.title}'. "
            f"Hãy xóa 'content block' khỏi bài học trước."
            f"'content block id': {block.lesson.id}"
        )

    # Nếu không vướng check ở trên, tức là quiz này là "mồ côi"
    # và user là superuser, cho phép xóa
    quiz.delete()
    return # Không trả về gì