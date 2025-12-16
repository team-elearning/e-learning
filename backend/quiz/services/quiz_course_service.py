# --- File mới: quiz_service.py ---
import uuid
from typing import Dict, Any, List
from django.db import transaction
from django.conf import settings
from django.db.models import Case, When, Prefetch
from django.utils import timezone
import random

from content.models import Quiz
from core.exceptions import DomainError
from progress.models import QuizAttempt, QuestionAnswer
from quiz.domains.quiz_domain import QuizDomain, QuestionDomain
from quiz.domains.quiz_attempt_domain import QuizAttemptDomain
from progress.domains.question_content_domain import QuestionContentDomain
from quiz.services.question_service import create_question, update_question, delete_question
from quiz.models import Question



UserModel = settings.AUTH_USER_MODEL


# ==========================================
# PUBLIC INTERFACE (CREATE)
# ==========================================

@transaction.atomic
def create_quiz(data: Dict[str, Any], actor: UserModel) -> QuizDomain:
    """
    Tạo Quiz và các Question con từ DTO.
    """
    questions_data = data.pop('questions', [])

    # 1. Tạo Quiz (object gốc)
    new_quiz = Quiz.objects.create(
        title=data.get('title', 'Bài tập không tiêu đề'),
        time_limit=data.get('time_limit') or None,
        time_open=data.get('time_open') or None,
        time_close=data.get('time_close') or None,
        owner=actor
    )
    
    # 2. Tạo Questions (con)
    for question_data in questions_data:
        create_question(quiz=new_quiz, data=question_data, actor=actor)

    quiz_with_questions = Quiz.objects.prefetch_related('questions').get(id=new_quiz.id)
    return QuizDomain.from_model(quiz_with_questions)


# ==========================================
# PUBLIC INTERFACE (UPDATE)
# ==========================================

@transaction.atomic
def update_quiz(quiz_id: uuid.UUID, data: Dict[str, Any]) -> QuizDomain:
    """
    Chỉ update các trường thông tin chung của Quiz.
    """
    try:
        # Select related course để check quyền sở hữu nếu cần
        # (Hoặc tin tưởng vào permission class ở View)
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        raise DomainError("Quiz không tồn tại.")

    # Update fields dynamic
    has_changes = False
    for field, value in data.items():
        if hasattr(quiz, field) and getattr(quiz, field) != value:
            setattr(quiz, field, value)
            has_changes = True
    
    if has_changes:
        quiz.save() # Django tự động chỉ update các field bị thay đổi nếu dùng logic thông minh, 
                    # hoặc dùng update_fields nếu muốn tối ưu cực đại.
    
    return QuizDomain.from_model(quiz)


# def get_quiz_details(quiz_id: uuid.UUID, user: UserModel) -> QuizDomain:
#     """
#     Lấy chi tiết 1 Quiz (lồng cả questions) và check quyền.
#     """
#     try:
#         # Tải sẵn 'questions' để QuizDomain.from_model có thể dùng
#         quiz = Quiz.objects.prefetch_related('questions').get(id=quiz_id)
#     except Quiz.DoesNotExist:
#         raise DomainError("Bài quiz không tìm thấy.")
        
#     # from_model giờ đã tự động lồng 'questions'
#     return QuizDomain.from_model(quiz)


# def get_quiz_content(quiz_id: uuid.UUID, user: UserModel) -> QuizDomain:
#     """
#     Lấy nội dung Quiz + Questions (Read-only).
#     Không xử lý trạng thái làm bài.
#     """
#     try:
#         # 1. Fetch Quiz & Prefetch Questions để tối ưu query
#         # Order by position để câu hỏi luôn ra đúng thứ tự soạn thảo
#         quiz = Quiz.objects.prefetch_related(
#             Prefetch('questions', queryset=Question.objects.order_by('position'))
#         ).get(id=quiz_id)

#     except Quiz.DoesNotExist:
#         raise DomainError("Bài học không tồn tại.")

#     # 3. Convert to Domain
#     return QuizDomain.from_model(quiz)


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
def delete_quiz(quiz_id: uuid.UUID) -> None:
    """
    Xóa Quiz. 
    Logic: Chỉ cho phép xóa khi Quiz KHÔNG được gắn vào bất kỳ ContentBlock nào.
    """
    # 1. Tìm Quiz
    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        raise DomainError("Không tìm thấy bài trắc nghiệm.")

    # 3. CHECK RÀNG BUỘC (Quan trọng)
    # Dùng related_name='content_blocks' từ model ContentBlock của bạn
    linked_blocks = quiz.content_blocks.all()

    if linked_blocks.exists():
        # Lấy tên bài học đầu tiên để báo lỗi cho chi tiết
        first_block = linked_blocks.first()
        lesson_title = first_block.lesson.title if first_block.lesson else "Bài học không tên"
        
        raise DomainError(
            f"Không thể xóa! Quiz này đang được dùng trong bài học: '{lesson_title}'. "
            "Vui lòng vào bài học gỡ bỏ Quiz này ra trước."
        )

    # 4. Nếu không vướng bận gì -> Xóa
    quiz.delete()