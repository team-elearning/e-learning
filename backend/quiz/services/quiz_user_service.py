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
from quiz.domains.quiz_attempt_domain import AttemptCreationResultDomain, QuizAttemptDomain, AttemptTakingDomain, QuestionTakingDomain, SaveAnswerResultDomain, SubmitAttemptResultDomain, AttemptResultDomain, QuestionReviewDomain



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
                is_answered=True if user_ans else False,
                is_flagged=user_ans.is_flagged if user_ans else False
            )
            taking_questions.append(taking_q_domain)

        # 5. Return Context Aggregate
        return AttemptTakingDomain(
            attempt_id=attempt.id,
            quiz_title=attempt.quiz.title,
            time_remaining_seconds=time_left,
            current_question_index=attempt.current_question_index,
            total_questions=len(taking_questions),
            questions=taking_questions,
        )


def save_answer(attempt_id, user, data: dict) -> SaveAnswerResultDomain:
    """
    Lưu câu trả lời.
    Input: Dictionary (Raw data đã validate).
    Output: Domain Entity.
    """
    # 1. Extract data từ dict (Không phụ thuộc Pydantic)
    question_id = data.get('question_id')
    current_index = data.get('current_index')
    selected_options = data.get('selected_options')
    is_flagged = data.get('is_flagged')

    # 2. Validate Logic
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=user)
    
    if attempt.status != 'in_progress':
        raise PermissionDenied("Bài thi đã kết thúc hoặc quá hạn.")

    # 3. Chuẩn bị data update
    defaults = {}
    if selected_options is not None:
        defaults['selected_options'] = selected_options
    if is_flagged is not None:
        defaults['is_flagged'] = is_flagged

    # 4. Upsert DB
    UserAnswer.objects.update_or_create(
        attempt=attempt,
        question_id=question_id,
        defaults=defaults
    )

    # 5. Update Current Index (Chỉ khi thay đổi)
    if current_index is not None and attempt.current_question_index != current_index:
        attempt.current_question_index = current_index
        attempt.save(update_fields=['current_question_index'])
        
    # 6. Return DOMAIN ENTITY (Không trả về DTO/JSON)
    return SaveAnswerResultDomain(
        status="saved",
        saved_at=timezone.now()
    )

##############################################################################################
##############################################################################################
##############################################################################################

def submit_attempt(attempt_id, user) -> SubmitAttemptResultDomain:
    """
    Xử lý nộp bài thi:
    1. Kiểm tra quyền sở hữu.
    2. Chốt thời gian.
    3. Tính điểm (Auto-grading).
    4. Cập nhật trạng thái DB.
    """
    # 1. Lấy Attempt & Validate
    try:
        attempt = QuizAttempt.objects.select_related('quiz').get(
            pk=attempt_id, 
            user=user
        )
    except QuizAttempt.DoesNotExist:
        raise ValidationError("Không tìm thấy bài thi hoặc bạn không có quyền.")

    # Logic Moodle: Nếu đã nộp rồi -> Trả về kết quả cũ luôn (Idempotency)
    # Tránh việc user refresh trang finish gây tính điểm lại.
    if attempt.status == 'completed':
        return SubmitAttemptResultDomain(
            attempt_id=attempt.id,
            status=attempt.status,
            score_obtained=attempt.score,
            passed=attempt.score >= (attempt.quiz.pass_score or 0),
            completion_time=attempt.time_submitted,
            message="Bài thi này đã được nộp trước đó."
        )

    # 2. Bắt đầu Transaction để chấm điểm
    with transaction.atomic():
        now = timezone.now()
        
        # 2.1. Tính điểm (Grading Engine)
        # Hàm này sẽ duyệt qua từng UserAnswer và so khớp với Question
        total_score = _calculate_total_score(attempt)
        
        # 2.2. Kiểm tra điều kiện Đạt/Trượt
        # Moodle logic: So sánh với pass_score của Quiz
        pass_score = attempt.quiz.pass_score or 0
        is_passed = total_score >= pass_score

        # 2.3. Update Attempt
        attempt.score = total_score
        attempt.status = 'completed'
        attempt.time_submitted = now
        attempt.save()

        # (Optional) TODO: Bắn event/signal cập nhật tiến độ khoá học (Course Progress)

    # 3. Return Domain
    return SubmitAttemptResultDomain(
        attempt_id=attempt.id,
        status='completed',
        score_obtained=total_score,
        passed=is_passed,
        completion_time=now,
        message="Nộp bài thành công."
    )


# --- PRIVATE HELPER: GRADING ENGINE ---
def _calculate_total_score( attempt) -> float:
    """
    Logic chấm điểm tự động.
    Tham khảo Moodle: Duyệt qua tất cả câu hỏi trong attempt, 
    load đáp án đúng và so sánh.
    """
    total_score = 0.0
    
    # Lấy danh sách câu trả lời của user cho attempt này
    # Dùng select_related('question') để lấy luôn đáp án đúng (trong question) đỡ query nhiều
    user_answers = UserAnswer.objects.filter(attempt=attempt).select_related('question')

    for ua in user_answers:
        question = ua.question
        user_selection = ua.selected_options # JSON/Dict

        # Logic chấm điểm từng câu (Delegated Grading)
        # Nên tách logic này ra Strategy Pattern nếu có nhiều loại câu hỏi (MCQ, Essay, FillBlank...)
        score_for_question = _grade_single_question(question, user_selection)
        
        # Cộng dồn
        total_score += score_for_question
        
        # Cập nhật điểm cho từng câu trả lời (để hiện thị detail sau này)
        ua.score_obtained = score_for_question
        ua.is_correct = (score_for_question > 0) # Logic đơn giản: có điểm là đúng
        ua.save(update_fields=['score_obtained', 'is_correct'])
        
    return total_score


def _grade_single_question( question, user_selection) -> float:
    """
    Hàm chấm điểm cho 1 câu hỏi cụ thể.
    Đây là phiên bản đơn giản cho Multiple Choice / Single Choice.
    """
    if not user_selection:
        return 0.0

    # Lấy đáp án đúng từ Question (giả sử lưu trong answer_payload)
    # Structure payload ví dụ: 
    # { "options": [{"id": "A", "text": "...", "is_correct": true}, ...] }
    correct_options = [
        opt['id'] for opt in question.answer_payload.get('options', []) 
        if opt.get('is_correct')
    ]
    
    # User selection ví dụ: ["A"] hoặc ["A", "B"]
    user_selected_ids = user_selection if isinstance(user_selection, list) else []

    # LOGIC CHẤM:
    # 1. Single Choice (Radio): Khớp hoàn toàn -> Max điểm
    # 2. Multiple Choice (Checkbox): Moodle thường tính: (Số đúng chọn - Số sai chọn)
    
    # Ở đây làm logic đơn giản nhất: EXACT MATCH (Khớp hoàn toàn mới có điểm)
    # Bạn có thể nâng cấp thành Partial Credit (điểm thành phần) sau.
    
    # So sánh 2 set (không quan tâm thứ tự)
    if set(correct_options) == set(user_selected_ids):
        # Nếu đúng, trả về điểm default của câu hỏi (thường là 1 hoặc setting trong Question)
        return 1.0 # Hoặc question.default_mark
        
    return 0.0


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


def get_attempt_result(self, attempt_id, user) -> AttemptResultDomain:
    """
    Lấy kết quả bài thi.
    Logic Moodle: Kiểm tra 'Review Options' (show_score, show_correct_answer)
    để quyết định xem user được nhìn thấy gì.
    """
    
    # 1. Fetch & Validate
    # Lấy attempt + quiz config
    try:
        attempt = QuizAttempt.objects.select_related('quiz').get(
            pk=attempt_id, 
            user=user
        )
    except QuizAttempt.DoesNotExist:
        raise PermissionDenied("Không tìm thấy bài thi.")

    # Check status: Phải nộp bài rồi mới được xem kết quả
    if attempt.status != 'completed':
        raise PermissionDenied("Bài thi chưa hoàn thành, không thể xem kết quả.")

    quiz = attempt.quiz
    
    # 2. Determine Visibility Rules (Logic quan trọng kiểu Moodle)
    # Exam Mode: Thường ẩn đáp án đúng, chỉ hiện điểm.
    # Practice Mode: Hiện tất cả.
    
    # Giả sử Quiz model có các cờ config sau (nếu chưa có bạn hãy coi như mặc định dựa theo mode)
    is_practice = (quiz.mode == 'practice')
    
    # Rule 1: Được xem đáp án đúng không?
    can_see_correct_answer = getattr(quiz, 'show_correct_answer', is_practice)
    
    # Rule 2: Được xem giải thích không?
    can_see_explanation = getattr(quiz, 'show_explanation', is_practice)
    
    # Rule 3: Được xem điểm chi tiết từng câu không? (Exam gắt có thể ẩn luôn cái này)
    can_see_detailed_score = True 

    # 3. Build Question Review List
    review_questions = []
    
    # Lấy tất cả câu hỏi theo thứ tự (logic giống lúc làm bài)
    question_ids = attempt.questions_order
    questions_map = {str(q.id): q for q in Question.objects.filter(id__in=question_ids)}
    
    # Lấy câu trả lời của user
    user_answers_map = {
        str(ua.question_id): ua 
        for ua in UserAnswer.objects.filter(attempt=attempt)
    }

    max_score_total = 0.0

    for q_id in question_ids:
        question = questions_map.get(q_id)
        if not question: 
            continue
            
        # Mặc định mỗi câu 1 điểm (hoặc lấy từ config question)
        question_max_score = 1.0 
        max_score_total += question_max_score
        
        user_ans = user_answers_map.get(q_id)
        
        # --- XỬ LÝ DỮ LIỆU NHẠY CẢM ---
        correct_ans_data = None
        explanation_data = None
        
        # Chỉ lấy đáp án đúng từ DB nếu được phép xem
        if can_see_correct_answer:
            # Trích xuất đáp án đúng từ payload (ví dụ lấy ID của option đúng)
            correct_ans_data = self._extract_correct_options(question)
        
        if can_see_explanation:
            explanation_data = question.answer_payload.get('explanation', '')

        # --- MAP TO DOMAIN ---
        review_q = QuestionReviewDomain(
            id=question.id,
            prompt=question.prompt,
            user_selected=user_ans.selected_options if user_ans else None,
            is_correct=user_ans.is_correct if user_ans else False,
            score_obtained=user_ans.score_obtained if user_ans else 0.0,
            
            # Fields có điều kiện
            correct_answer=correct_ans_data,
            explanation=explanation_data
        )
        review_questions.append(review_q)

    # 4. Return Aggregate Result
    # Tính thời gian làm bài
    time_taken = 0
    if attempt.time_submitted and attempt.time_start:
        time_taken = int((attempt.time_submitted - attempt.time_start).total_seconds())

    return AttemptResultDomain(
        attempt_id=attempt.id,
        quiz_title=quiz.title,
        status=attempt.status,
        time_taken_seconds=time_taken,
        time_submitted=attempt.time_submitted,
        score_obtained=attempt.score,
        max_score=max_score_total,
        is_passed=attempt.score >= (quiz.pass_score or 0),
        questions=review_questions
    )


# --- HELPER EXTRACTOR ---
def _extract_correct_options(self, question):
    """
    Helper để lấy ra list các Option đúng từ JSON payload của câu hỏi.
    """
    try:
        options = question.answer_payload.get('options', [])
        # Lọc các option có flag is_correct=True
        return [opt['id'] for opt in options if opt.get('is_correct')]
    except Exception:
        return []
