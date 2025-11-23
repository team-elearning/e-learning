from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
import random
from django.db.models import Max

from core.exceptions import ExamNotFoundError
from quiz.models import Quiz, QuizAttempt, UserAnswer, Question
from quiz.domains.quiz_preflight_domain import AccessDecisionDomain, QuizPreflightDomain, AttemptHistoryItemDomain
from quiz.domains.exam_domain import ExamDomain



# ==========================================
# PUBLIC INTERFACE (HELPER)
# ==========================================

def _validate_new_attempt_rules( quiz, user):
    """ Hàm nội bộ check rule chặt chẽ trước khi insert DB """
    now = timezone.now()
    
    if quiz.time_open and now < quiz.time_open:
        raise ValidationError("Bài thi chưa mở.")
        
    if quiz.time_close and now > quiz.time_close:
        raise ValidationError("Bài thi đã quá hạn.")
        
    if quiz.max_attempts:
        count = QuizAttempt.objects.filter(quiz=quiz, user=user).count()
        if count >= quiz.max_attempts:
            raise ValidationError("Bạn đã hết lượt làm bài.")


def _is_time_up( attempt, quiz):
    if not quiz.time_limit:
        return False
    elapsed = timezone.now() - attempt.time_start
    # Cho phép du di thêm vài giây (network latency tolerance giống Moodle)
    return elapsed.total_seconds() > (quiz.time_limit.total_seconds() + 5)


# def _check_answer( question, user_selection):
#     # Logic so sánh đáp án user_selection với question.answer_payload
#     # Return True/False
#     return False # Placeholder


def _evaluate_access_rules(exam: ExamDomain, attempts_count: int, ongoing_attempt) -> AccessDecisionDomain:
        """
        Engine kiểm tra điều kiện. Trả về AccessDecisionDomain.
        """

        # Ưu tiên 1: Resume (Luôn cho phép nếu đang làm dở)
        if ongoing_attempt:
            return AccessDecisionDomain(
                is_allowed=True,
                action="resume",
                reason_message="Bạn đang có bài thi chưa nộp.",
                button_label="Tiếp tục làm bài",
                ongoing_attempt_id=ongoing_attempt.id
            )

        # Ưu tiên 2: Check Thời gian (Time Window)
        if exam.status_label == "upcoming":
            return AccessDecisionDomain(
                is_allowed=False,
                reason_message=f"Bài thi sẽ mở vào lúc {exam.time_open}",
                button_label="Chưa mở"
            )
        
        if exam.status_label == "closed":
            return AccessDecisionDomain(
                is_allowed=False,
                reason_message="Bài thi đã đóng.",
                button_label="Đã đóng"
            )

        # Ưu tiên 3: Check số lượt (Attempts Limit)
        if exam.max_attempts and exam.max_attempts > 0 and attempts_count >= exam.max_attempts:
            return AccessDecisionDomain(
                is_allowed=False,
                reason_message="Bạn đã hết {exam.max_attempts} lượt làm bài cho phép.",
                button_label="Hết lượt"
            )

        # Default: Cho phép thi mới
        return AccessDecisionDomain(
            is_allowed=True,
            action="start",
            reason_message="Sẵn sàng",
            button_label="Bắt đầu làm bài"
        )


# ==========================================
# PUBLIC INTERFACE (SERVICE)
# ==========================================

def get_preflight_info(quiz_id, user) -> QuizPreflightDomain:
    """
    Lấy toàn bộ thông tin màn hình chờ.
    Moodle logic: Kiểm tra toàn bộ 'access rules' và trả về trạng thái UI.
    """
    try:
        quiz = Quiz.objects.get(pk=quiz_id)
    except Quiz.DoesNotExist:
        raise ExamNotFoundError("Không tìm thấy bài thi.")

    # 1. Lấy dữ liệu lịch sử (Context)
    attempts = QuizAttempt.objects.filter(quiz=quiz, user=user)
    attempts_count = attempts.count()
    ongoing_attempt = attempts.filter(status='in_progress').first()

    score_best = 0.0
    completed_attempts = attempts.filter(status='completed')
    if completed_attempts.exists():
        max_val = completed_attempts.aggregate(Max('score'))['score__max']
        score_best = float(max_val) if max_val is not None else 0.0

    # === [NEW] XÂY DỰNG LỊCH SỬ (HISTORY LIST) ===
    history_list = []
    for index, att in enumerate(attempts, start=1):
        # Convert từng Model -> Domain Item
        item = AttemptHistoryItemDomain(
            id=str(att.id),
            order=index,             # Lần 1, Lần 2...
            status=att.status,
            score=float(att.score) if att.score is not None else None,
            time_submitted=att.time_submitted
        )
        history_list.append(item)

    exam_domain = ExamDomain.from_model_overview(quiz)
    
    decision = _evaluate_access_rules(exam_domain, attempts_count, ongoing_attempt)
    
    return QuizPreflightDomain(
            exam=exam_domain,
            access_decision=decision,
            attempts_used=attempts_count,
            score_best=round(score_best, 2),
            history=history_list
        )


@transaction.atomic
def start_or_resume_attempt( quiz_id, user):
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
    ).select_for_update().first()
    # select_for_update: Khóa dòng này lại, tránh user click 2 lần gây lỗi

    if ongoing_attempt:
        # Kiểm tra nếu quá hạn giờ làm bài (Real-time check)
        if _is_time_up(ongoing_attempt, quiz):
            ongoing_attempt.status = 'overdue'
            ongoing_attempt.save()
            raise ValidationError("Bài làm trước đó đã hết thời gian.")
        return ongoing_attempt, "resumed"

    # 2. Nếu tạo mới -> Validate lại điều kiện (Deep Validate)
    # Tại sao check lại? Vì từ lúc load trang Info đến lúc bấm nút Start,
    # có thể bài thi vừa đóng hoặc user vừa login ở tab khác làm hết lượt.
    _validate_new_attempt_rules(quiz, user)

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


# def save_answer(attempt_id, question_id, selected_options, user):
#     """
#     Auto-save từng câu.
#     """
#     attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=user)
    
#     if attempt.status != 'in_progress':
#         raise PermissionDenied("Không thể lưu câu trả lời cho bài thi đã kết thúc.")

#     # Upsert câu trả lời
#     UserAnswer.objects.update_or_create(
#         attempt=attempt,
#         question_id=question_id,
#         defaults={'selected_options': selected_options}
#     )
#     # Update vị trí làm bài hiện tại để resume chính xác
#     # (Cần logic tìm index của question_id trong questions_order)
#     try:
#         idx = attempt.questions_order.index(str(question_id)) # JSON list thường lưu string UUID
#         attempt.current_question_index = idx
#         attempt.save(update_fields=['current_question_index'])
#     except ValueError:
#         pass


# def submit_attempt( attempt_id, user):
#     """
#     Nộp bài: Tính điểm, đổi status.
#     """
#     attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=user)
#     if attempt.status != 'in_progress':
#         return attempt # Đã nộp rồi

#     # Logic chấm điểm (Giả lập đơn giản)
#     total_score = 0
    
#     # Lấy tất cả câu trả lời
#     user_answers = UserAnswer.objects.filter(attempt=attempt)
#     questions_map = {str(q.id): q for q in Question.objects.filter(id__in=attempt.questions_order)}

#     for ua in user_answers:
#         question = questions_map.get(str(ua.question_id))
#         if question:
#             # Gọi hàm so sánh đáp án (cần viết riêng trong Question model hoặc Utils)
#             is_correct = _check_answer(question, ua.selected_options)
#             ua.is_correct = is_correct
#             if is_correct:
#                 # Giả sử mỗi câu 1 điểm hoặc lấy từ config
#                 ua.score_obtained = 1 
#                 total_score += 1
#             else:
#                 ua.score_obtained = 0
#             ua.save()
    
#     attempt.score = total_score
#     attempt.time_submitted = timezone.now()
#     attempt.status = 'completed'
#     attempt.save()
    
#     return attempt
