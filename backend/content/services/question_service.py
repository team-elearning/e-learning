import uuid
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.conf import settings

from content.models import Quiz, Question
from content.domains.question_domain import QuestionDomain
from core.exceptions import DomainError



UserModel = settings.AUTH_USER_MODEL

@transaction.atomic
def create_question(quiz: Quiz, data: Dict[str, Any]) -> QuestionDomain:
    """
    Tạo MỘT Question cho một Quiz.
    Hàm này được gọi bởi 'quiz_service.create_quiz'
    hoặc 'quiz_service.patch_quiz'.
    """
    new_q = Question.objects.create(
        quiz=quiz,
        position=data.get('position', 0),
        type=data.get('type', 'multiple_choice_single'),
        prompt=data.get('prompt', {}),
        answer_payload=data.get('answer_payload', {}),
        hint=data.get('hint', {})
    )
    return QuestionDomain.from_model(new_q)


@transaction.atomic
def patch_question(question_id: uuid.UUID, data: Dict[str, Any]) -> QuestionDomain:
    """
    Cập nhật (vá) MỘT Question.
    Hàm này được gọi bởi 'quiz_service.patch_quiz'.
    """
    try:
        q_to_update = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        raise DomainError(f"Question {question_id} không tìm thấy để cập nhật.")

    # Lấy các trường có thể patch từ model của bạn
    # (position được gán ở service cha)
    if 'position' in data: 
        q_to_update.position = data['position']
    if 'type' in data: 
        q_to_update.type = data['type']
    if 'prompt' in data: 
        q_to_update.prompt = data['prompt']
    if 'answer_payload' in data: 
        q_to_update.answer_payload = data['answer_payload']
    if 'hint' in data: 
        q_to_update.hint = data['hint']
    
    q_to_update.save()
    return QuestionDomain.from_model(q_to_update)


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


def list_questions_for_quiz(quiz_id: uuid.UUID) -> List[QuestionDomain]:
    """
    Lấy danh sách các Question (dưới dạng Domain) cho 1 Quiz.
    """
    questions = Question.objects.filter(quiz_id=quiz_id).order_by('position')
    return [QuestionDomain.from_model(q) for q in questions]