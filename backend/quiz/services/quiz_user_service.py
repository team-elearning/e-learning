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
from quiz.domains.quiz_attempt_domain import AttemptCreationResultDomain, QuizAttemptDomain, AttemptTakingDomain, QuestionTakingDomain



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
def start_or_resume_attempt(quiz_id, user, data: dict):
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
    ).select_for_update().first() # select_for_update: Khóa dòng này lại, tránh user click 2 lần gây lỗi

    if ongoing_attempt:
        # Kiểm tra nếu quá hạn giờ làm bài (Real-time check)
        if _is_time_up(ongoing_attempt, quiz):
            ongoing_attempt.status = 'overdue'
            ongoing_attempt.save()
            raise ValidationError("Bài làm trước đó đã hết thời gian.")
        return AttemptCreationResultDomain(
                attempt=QuizAttemptDomain.from_model(ongoing_attempt),
                action="resumed",
                detail="Đã khôi phục bài làm dang dở."
            )

    # 2. Nếu tạo mới -> Validate lại điều kiện (Deep Validate)
    # Tại sao check lại? Vì từ lúc load trang Info đến lúc bấm nút Start,
    # có thể bài thi vừa đóng hoặc user vừa login ở tab khác làm hết lượt.
    _validate_new_attempt_rules(quiz, user)

    # 3. Tạo mới (Random câu hỏi)
    all_questions_ids = [str(uid) for uid in quiz.questions.values_list('id', flat=True)]
    
    if quiz.shuffle_questions:
        random.shuffle(all_questions_ids)
    
    # Cắt bớt nếu có limit số câu
    if quiz.questions_count > 0:
        all_questions_ids = all_questions_ids[:quiz.questions_count]

    new_attempt = QuizAttempt.objects.create(
        user=user,
        quiz=quiz,
        questions_order=all_questions_ids, # Snapshot đề thi
        status='in_progress',
        current_question_index=0
    )
    
    # Return Domain: CREATED
    return AttemptCreationResultDomain(
        attempt=QuizAttemptDomain.from_model(new_attempt),
        action="created",
        detail="Bắt đầu bài làm mới."
    )


def get_attempt_taking_context(attempt_id, user) -> AttemptTakingDomain:
        """
        Lấy ngữ cảnh làm bài thi (Resume/Start).
        Logic Moodle: Load 'layout', load 'timelimit', load 'question_usage'.
        """
        # 1. Validate Ownership & Status
        attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=user)
        
        if attempt.status != 'in_progress':
            # Nếu đã nộp rồi mà cố vào lại -> Nên throw lỗi hoặc redirect sang trang kết quả
            # Ở đây ta throw lỗi để View xử lý
            raise PermissionDenied("Bài thi này đã kết thúc.")

        # 2. Tính thời gian còn lại (Server Side Calculation)
        # Tránh tin tưởng đồng hồ client
        time_left = None
        if attempt.quiz.time_limit:
            elapsed = timezone.now() - attempt.time_start
            limit_seconds = attempt.quiz.time_limit.total_seconds()
            # Trừ thêm độ trễ mạng (latency buffer) khoảng 2-3s nếu cần
            remaining = limit_seconds - elapsed.total_seconds()
            time_left = max(0, int(remaining))

        # 3. Lấy danh sách câu hỏi theo Snapshot Order
        # Lưu ý: questions_order là List[str] (ID)
        question_ids = attempt.questions_order 
        
        # Query 1 lần lấy hết câu hỏi (Unordered)
        questions_qs = Question.objects.filter(id__in=question_ids)
        questions_map = {str(q.id): q for q in questions_qs}

        # Query 1 lần lấy hết câu trả lời đã lưu (Saved Answers)
        user_answers_qs = UserAnswer.objects.filter(attempt=attempt)
        answers_map = {str(ua.question_id): ua for ua in user_answers_qs}

        # 4. MERGE & RE-ORDER (Tái tạo đề thi)
        # Loop theo đúng thứ tự trong questions_order
        taking_questions = []
        
        for q_id in question_ids:
            question_obj = questions_map.get(q_id)
            if not question_obj:
                continue # Skip nếu câu hỏi bị xóa khỏi DB (Edge case)

            # Tìm câu trả lời cũ (nếu có)
            user_ans = answers_map.get(q_id)
            
            # Map sang Domain
            taking_q_domain = QuestionTakingDomain(
                id=question_obj.id,
                type=question_obj.type,
                prompt=question_obj.prompt,
                
                # Rehydrate State (Khôi phục trạng thái)
                current_selection=user_ans.selected_options if user_ans else None,
                is_answered=True if user_ans else False
            )
            taking_questions.append(taking_q_domain)

        # 5. Return Context Aggregate
        return AttemptTakingDomain(
            attempt_id=attempt.id,
            quiz_title=attempt.quiz.title,
            time_remaining_seconds=time_left,
            current_question_index=attempt.current_question_index,
            total_questions=len(taking_questions),
            questions=taking_questions
        )


# def save_answer(self, attempt_id, user, input_dto: SaveAnswerInput) -> SaveAnswerOutput:
#     """
#     Lưu câu trả lời và trạng thái Flag.
#     """
#     # 1. Validate Attempt
#     # Dùng select_related/only để tối ưu query nếu cần
#     attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=user)
    
#     if attempt.status != 'in_progress':
#         raise ValidationError("Bài thi đã kết thúc hoặc quá hạn.")

#     # 2. Chuẩn bị dữ liệu update
#     # Chúng ta dùng update_or_create để xử lý cả case chưa có và đã có
#     defaults = {}
    
#     # Chỉ update nếu client có gửi dữ liệu lên (tránh ghi đè None vào data đang có)
#     if input_dto.selected_options is not None:
#         defaults['selected_options'] = input_dto.selected_options
        
#     if input_dto.is_flagged is not None:
#         defaults['is_flagged'] = input_dto.is_flagged

#     # 3. Upsert UserAnswer
#     # Logic: Tìm theo (attempt, question_id). Nếu thấy -> Update 'defaults'. Chưa -> Create.
#     UserAnswer.objects.update_or_create(
#         attempt=attempt,
#         question_id=input_dto.question_id,
#         defaults=defaults
#     )

#     # 4. Update vị trí hiện tại (Current Index)
#     # Chỉ save khi có sự thay đổi để giảm tải DB write
#     if attempt.current_question_index != input_dto.current_index:
#         attempt.current_question_index = input_dto.current_index
#         attempt.save(update_fields=['current_question_index'])
        
#     # 5. Return Output DTO
#     return SaveAnswerOutput(
#         status="saved",
#         saved_at=timezone.now()
#     )


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
