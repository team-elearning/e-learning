import uuid
from typing import Dict, Any, List
from django.db import transaction
from django.conf import settings

from content.domains.question_domain import QuestionDomain
from core.exceptions import DomainError
from media.services.file_service import commit_files_by_ids_for_object
from quiz.models import Quiz, Question



UserModel = settings.AUTH_USER_MODEL


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


@transaction.atomic
def create_question(quiz: Quiz, data: Dict[str, Any], actor: UserModel) -> QuestionDomain:
    # 1. Tạo Question
    new_q = Question.objects.create(
        quiz=quiz,
        position=data.get('position', 0),
        type=data.get('type', 'multiple_choice_single'),
        prompt=data.get('prompt', {}),
        answer_payload=data.get('answer_payload', {}),
        hint=data.get('hint', {})
    )

    # 2. Thu thập tất cả file ID có trong question này
    # Quét từ prompt (đề bài), answer (đáp án), hint (gợi ý)
    file_ids_to_commit = []
    file_ids_to_commit.extend(_extract_file_ids_from_json(new_q.prompt))
    file_ids_to_commit.extend(_extract_file_ids_from_json(new_q.answer_payload))
    file_ids_to_commit.extend(_extract_file_ids_from_json(new_q.hint))

    # 3. Commit file và GẮN VÀO QUESTION (Quan trọng)
    if file_ids_to_commit:
        # Lưu ý: actor lấy ở đâu? 
        # Tốt nhất nên truyền actor từ create_quiz xuống, hoặc tạm thời để None
        # (Nếu để None thì logic commit của bạn cần cho phép owner của Quiz hoặc Course)
        
        # Vì Question chưa có field 'owner', hàm commit cần check quyền dựa trên cha (Quiz/Course)
        # Hoặc đơn giản: Question thuộc Quiz, Quiz thuộc ai thì người đó có quyền.
        
        commit_files_by_ids_for_object(
            file_ids=file_ids_to_commit,
            related_object=new_q,  # File này thuộc về QUESTION, không phải Course
            actor=actor # Cần refactor để truyền actor xuống nếu muốn check chặt
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