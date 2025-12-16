import uuid
from typing import Dict, Any, List
from django.db import transaction
from django.conf import settings
from django.db.models import Case, When, Prefetch
from django.utils import timezone
import random

from core.exceptions import DomainError
from quiz.models import Quiz, Question
from progress.models import QuizAttempt, QuestionAnswer
from progress.domains.quiz_attempt_domain import QuizAttemptDomain
from progress.domains.question_content_domain import QuestionContentDomain
from progress.domains.question_submission_domain import QuestionSubmissionDomain



# ==========================================
# PUBLIC INTERFACE (HELPER)
# ==========================================

def evaluate_answer(question, user_answer_data):
    """
    Trả về: (score, is_correct, feedback)
    """
    max_score = question.default_score if hasattr(question, 'default_score') else 1.0
    
    # Lấy cấu hình đáp án đúng từ Question (Giả sử bạn lưu trong field `correct_answer_config`)
    # Structure VD: {"correct_ids": ["uuid-1"], "explanation": "Vì A là..."}
    correct_config = question.correct_answer_config 
    
    if question.type == 'multiple_choice_single':
        user_selected = user_answer_data.get('selected_ids', [])
        correct_ids = correct_config.get('correct_ids', [])
        
        # Logic so sánh đơn giản:
        if set(user_selected) == set(correct_ids):
            return max_score, True, correct_config.get('explanation', 'Chính xác!')
        else:
            return 0.0, False, correct_config.get('explanation', 'Sai rồi.')

    elif question.type == 'fill_in_the_blank':
        user_text = user_answer_data.get('text', '').strip().lower()
        accepted_answers = [a.lower() for a in correct_config.get('accepted_texts', [])]
        
        if user_text in accepted_answers:
            return max_score, True, "Chính xác"
        return 0.0, False, "Sai rồi"

    # ... Implement các loại câu hỏi khác ...

    return 0.0, False, "Chưa hỗ trợ chấm loại câu hỏi này"

def get_correct_answer_for_display(question):
    """
    Helper để lấy đáp án đúng trả về cho Frontend hiển thị (khi làm mode Practice)
    """
    # Chỉ trả về những gì Frontend cần để tô xanh đáp án đúng
    return question.correct_answer_config


# ==========================================
# PUBLIC INTERFACE (GET)
# ==========================================

@transaction.atomic
def start_or_resume_attempt(quiz_id: uuid.UUID, user):
    # 1. Tìm bài đang làm dở
    attempt = QuizAttempt.objects.filter(
        user=user, 
        quiz_id=quiz_id, 
        status='in_progress'
    ).first()

    if not attempt:
        # 2. Nếu không có, tạo mới (New Attempt)
        quiz = Quiz.objects.get(id=quiz_id)

        # --- LOGIC RANDOM CÂU HỎI TẠI ĐÂY ---
        # Lấy tất cả ID câu hỏi của Quiz
        all_q_ids = list(quiz.questions.values_list('id', flat=True))

        # Lấy số lượng câu theo cấu hình
        count = quiz.questions_count if 0 < quiz.questions_count < len(all_q_ids) else len(all_q_ids)
        selected_ids = random.sample(all_q_ids, count)

        # Xử lý: Đảo vị trí (Shuffle)
        if quiz.shuffle_questions:
            random.shuffle(selected_ids)
        
        attempt = QuizAttempt.objects.create(
            user=user, 
            quiz=quiz,
            questions_order=[str(uid) for uid in selected_ids], # Lưu cứng thứ tự
            attempt_mode=quiz.mode
        )
    
    return QuizAttemptDomain.from_model(attempt)


def get_question_in_attempt(attempt_id: uuid.UUID, question_id: uuid.UUID, user) -> QuestionContentDomain:
    """
    Lấy nội dung 1 câu hỏi cụ thể trong ngữ cảnh attempt.
    Xử lý Shuffle Options (Câu trả lời) tại đây.
    """
    # Validate xem question_id có nằm trong attempt này không
    try:
        attempt = QuizAttempt.objects.get(id=attempt_id, user=user)
    except QuizAttempt.DoesNotExist:
        raise DomainError("Không tìm thấy bài làm.")
    
    if str(question_id) not in attempt.questions_order:
        raise DomainError("Câu hỏi không thuộc bài làm này")

    question = Question.objects.get(id=question_id)
    
    # 2. --- LOGIC MỚI: TÌM CÂU TRẢ LỜI CŨ (RESUME) ---
    # Tìm xem user đã từng trả lời câu này chưa
    # Dùng filter().first() để tránh lỗi nếu chưa có record
    existing_answer = QuestionAnswer.objects.filter(
        attempt=attempt, 
        question=question
    ).first()

    # Nếu có thì lấy data, chưa có thì trả về rỗng
    saved_answer_data = existing_answer.answer_data if existing_answer else {}
    saved_flag_status = existing_answer.is_flagged if existing_answer else False

    # --- Logic Random Đáp Án (Option Shuffle) ---
    raw_options = question.prompt.get('options', [])
    
    # Để đảm bảo user F5 không bị đổi thứ tự đáp án liên tục, 
    # ta dùng seed = attempt_id + question_id
    seed_val = str(attempt.id) + str(question.id)
    random.seed(seed_val) 
    
    shuffled_options = raw_options.copy()
    random.shuffle(shuffled_options)
    
    return QuestionContentDomain(
        id=question.id,
        type=question.type,
        prompt_text=question.prompt.get('text', ''),
        prompt_image=question.prompt.get('image', None),
        options=shuffled_options,
        current_answer=saved_answer_data, 
        is_flagged=saved_flag_status
    )


# ==========================================
# PUBLIC INTERFACE (SUBMIT)
# ==========================================

@transaction.atomic
def submit_single_question(
    attempt_id: uuid.UUID, 
    submission: dict, 
    user
) -> QuestionSubmissionDomain:
    
    # 1. Validate Attempt
    try:
        attempt = QuizAttempt.objects.select_related('quiz').get(id=attempt_id, user=user)
    except QuizAttempt.DoesNotExist:
        raise DomainError("Không tìm thấy bài làm.")

    if attempt.status != 'in_progress':
        raise DomainError("Bài làm đã kết thúc, không thể nộp thêm.")

    if str(submission.question_id) not in attempt.questions_order:
        raise DomainError("Câu hỏi không thuộc bài làm này.")

    # 2. Lấy câu hỏi gốc
    question = Question.objects.get(id=submission.question_id)

    # 3. --- CHẤM ĐIỂM (GRADING LOGIC) ---
    # Tách logic chấm điểm ra hàm riêng để code gọn và dễ mở rộng
    score_achieved, is_correct, system_feedback = evaluate_answer(question, submission.answer_data)

    # 4. Lưu/Cập nhật vào bảng QuestionAnswer
    # Dùng update_or_create vì user có thể chọn lại đáp án nhiều lần trước khi nộp bài
    question_answer, created = QuestionAnswer.objects.update_or_create(
        attempt=attempt,
        question=question,
        defaults={
            'question_type': question.type,
            'answer_data': submission.answer_data,
            'is_flagged': False, # Reset flag nếu user đã nộp
            'score': score_achieved,
            'is_correct': is_correct,
            'feedback': system_feedback 
        }
    )

    # 5. Xử lý Output dựa trên Mode
    # Nếu là Exam (Kiểm tra): Có thể giấu kết quả đúng đi để tránh lộ đề
    show_result = True 
    if attempt.attempt_mode == 'exam':
         # Tùy logic: Exam có thể vẫn hiện đúng/sai nhưng ko hiện đáp án đúng, 
         # hoặc không hiện gì cả. Ở đây giả sử Exam thì giấu đáp án đúng.
         correct_answer_display = None
    else:
         # Practice: Hiện đáp án đúng luôn
         correct_answer_display = get_correct_answer_for_display(question)

    return QuestionSubmissionDomain(
        question_id=question.id,
        is_correct=is_correct,
        score=score_achieved,
        feedback=system_feedback if show_result else None,
        correct_answer_data=correct_answer_display if show_result else None
    )