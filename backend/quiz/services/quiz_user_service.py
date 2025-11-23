from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
import random

from quiz.models import Quiz, QuizAttempt, UserAnswer, Question



def get_quiz_info(self, quiz_id, user):
    """
    Trả về thông tin quiz và metadata của user (đã làm mấy lần, điểm cao nhất...)
    để hiển thị màn hình Pre-flight.
    """
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    attempts = QuizAttempt.objects.filter(quiz=quiz, user=user)
    
    # Check điều kiện
    can_attempt = True
    reason = None
    
    if quiz.time_close and timezone.now() > quiz.time_close:
        can_attempt = False
        reason = "Bài thi đã đóng."
    
    if quiz.max_attempts and attempts.count() >= quiz.max_attempts:
        # Check xem có bài nào đang dang dở không (Resume)
        if not attempts.filter(status='in_progress').exists():
            can_attempt = False
            reason = "Hết lượt làm bài."

    return {
        "quiz": quiz,
        "attempts_history": attempts, # Serializer sẽ lo việc format
        "can_attempt": can_attempt,
        "reason": reason
    }

def start_or_resume_attempt(self, quiz_id, user):
    """
    Logic:
    1. Tìm xem có attempt nào đang 'in_progress' không? -> Có thì Resume.
    2. Nếu không, kiểm tra điều kiện (hạn giờ, số lần).
    3. Tạo attempt mới: Random câu hỏi, snapshot thứ tự.
    """
    quiz = get_object_or_404(Quiz, pk=quiz_id)

    # 1. Check Resume
    ongoing_attempt = QuizAttempt.objects.filter(
        quiz=quiz, user=user, status='in_progress'
    ).first()

    if ongoing_attempt:
        # Kiểm tra nếu quá hạn giờ làm bài (Real-time check)
        if self._is_time_up(ongoing_attempt, quiz):
            ongoing_attempt.status = 'overdue'
            ongoing_attempt.save()
            raise ValidationError("Bài làm trước đó đã hết thời gian.")
        return ongoing_attempt, "resumed"

    # 2. Check điều kiện để tạo mới
    # (Check time_open, time_close, max_attempts tương tự hàm get_quiz_info)
    # ... code check ...

    # 3. Tạo mới (Random câu hỏi)
    all_questions_ids = list(quiz.questions.values_list('id', flat=True))
    
    if quiz.shuffle_questions:
        random.shuffle(all_questions_ids)
    
    # Cắt bớt nếu có limit số câu
    if quiz.questions_count > 0:
        all_questions_ids = all_questions_ids[:quiz.questions_count]

    new_attempt = QuizAttempt.objects.create(
        user=user,
        quiz=quiz,
        questions_order=all_questions_ids, # Snapshot đề thi
        status='in_progress'
    )
    return new_attempt, "created"

def save_answer(self, attempt_id, question_id, selected_options, user):
    """
    Auto-save từng câu.
    """
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=user)
    
    if attempt.status != 'in_progress':
        raise PermissionDenied("Không thể lưu câu trả lời cho bài thi đã kết thúc.")

    # Upsert câu trả lời
    UserAnswer.objects.update_or_create(
        attempt=attempt,
        question_id=question_id,
        defaults={'selected_options': selected_options}
    )
    # Update vị trí làm bài hiện tại để resume chính xác
    # (Cần logic tìm index của question_id trong questions_order)
    try:
        idx = attempt.questions_order.index(str(question_id)) # JSON list thường lưu string UUID
        attempt.current_question_index = idx
        attempt.save(update_fields=['current_question_index'])
    except ValueError:
        pass

def submit_attempt(self, attempt_id, user):
    """
    Nộp bài: Tính điểm, đổi status.
    """
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=user)
    if attempt.status != 'in_progress':
        return attempt # Đã nộp rồi

    # Logic chấm điểm (Giả lập đơn giản)
    total_score = 0
    
    # Lấy tất cả câu trả lời
    user_answers = UserAnswer.objects.filter(attempt=attempt)
    questions_map = {str(q.id): q for q in Question.objects.filter(id__in=attempt.questions_order)}

    for ua in user_answers:
        question = questions_map.get(str(ua.question_id))
        if question:
            # Gọi hàm so sánh đáp án (cần viết riêng trong Question model hoặc Utils)
            is_correct = self._check_answer(question, ua.selected_options)
            ua.is_correct = is_correct
            if is_correct:
                # Giả sử mỗi câu 1 điểm hoặc lấy từ config
                ua.score_obtained = 1 
                total_score += 1
            else:
                ua.score_obtained = 0
            ua.save()
    
    attempt.score = total_score
    attempt.time_submitted = timezone.now()
    attempt.status = 'completed'
    attempt.save()
    
    return attempt

def _is_time_up(self, attempt, quiz):
    if not quiz.time_limit:
        return False
    elapsed = timezone.now() - attempt.time_start
    return elapsed > quiz.time_limit

def _check_answer(self, question, user_selection):
    # Logic so sánh đáp án user_selection với question.answer_payload
    # Return True/False
    return False # Placeholder