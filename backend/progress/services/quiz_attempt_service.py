import logging
import random
import uuid
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from typing import Optional

from core.exceptions import DomainError
from content.models import Enrollment
from quiz.models import Quiz, Question
from progress.models import QuizAttempt, QuestionAnswer
from progress.domains.quiz_attempt_domain import QuizAttemptDomain
from progress.services.question_attempt_service import evaluate_answer



logger = logging.getLogger(__name__)

# ==========================================
# PUBLIC INTERFACE (HELPER)
# ==========================================

# def _build_result_domain(attempt) -> QuizAttemptDomain:
#     time_taken = 0
#     if attempt.time_submitted and attempt.time_start:
#         time_taken = int((attempt.time_submitted - attempt.time_start).total_seconds())

#     return QuizAttemptDomain(
#         id=attempt.id,
#         status=attempt.status,
#         score=attempt.score,
#         max_score=attempt.max_score,
#         is_passed=attempt.is_passed,
#         time_taken_seconds=time_taken,
#         completed_at=attempt.time_submitted
#     )

# def start_quiz_attempt(user, quiz_id: str) -> QuizAttemptDomain:
#     """
#     Xử lý logic bắt đầu làm bài.
#     Moodle logic: Check access rules -> Check existing -> Create/Resume.
#     """
#     # 1. Lấy thông tin Quiz (Dùng select_related nếu cần)
#     quiz = get_object_or_404(Quiz, id=quiz_id)
#     now = timezone.now()

#     # --- A. ACCESS RULES CHECK (Luật truy cập) ---
    
#     # 1. Check thời gian mở/đóng đề
#     if quiz.time_open and now < quiz.time_open:
#         raise ValueError(f"Bài thi chưa mở. Vui lòng quay lại vào {quiz.time_open}.")
        
#     if quiz.time_close and now > quiz.time_close:
#         raise ValueError("Bài thi đã kết thúc. Bạn không thể bắt đầu lượt làm mới.")

#     # --- B. RESUME LOGIC (Học theo Moodle) ---
#     # Kiểm tra xem user có bài đang làm dở không?
#     existing_attempt = QuizAttempt.objects.filter(
#         user=user,
#         quiz_id=quiz.id,
#         status='in_progress'
#     ).first()

#     attempt_model = None

#     if existing_attempt:
#         # Nếu còn thời gian (chưa hết giờ) -> Cho Resume
#         # Nếu đã hết giờ (do job cleanup chưa chạy) -> Đánh dấu nộp bài và chặn.
#         if _is_attempt_expired(existing_attempt, quiz):
#             # Auto submit bài cũ (Logic xử lý sau)
#             existing_attempt.status = 'submitted'
#             existing_attempt.finished_at = now
#             existing_attempt.save()
#         else:
#             # Return bài cũ để user làm tiếp
#             return existing_attempt

#     # 3. Create New Logic
#         if not attempt_model:
#             # Check limit attempts
#             completed_count = QuizAttempt.objects.filter(
#                 user=user, quiz_id=quiz.id, status__in=['submitted', 'graded']
#             ).count()
            
#             if quiz.max_attempts > 0 and completed_count >= quiz.max_attempts:
#                 raise ValueError(f"Bạn đã hết số lượt làm bài cho phép ({quiz.max_attempts}).")

#             with transaction.atomic():
#                 attempt_model = QuizAttempt.objects.create(
#                     user=user,
#                     quiz_id=quiz.id,
#                     status='in_progress',
#                     max_score=quiz.total_score or 10.0
#                 )
#                 # TODO: _generate_questions(attempt_model, quiz)

#         # 4. CONVERT TO DOMAIN & RETURN
#         # Service không trả về Model, mà trả về Domain đã được tính toán remaining_seconds
#         return QuizAttemptDomain.from_model(attempt_model, quiz)

# def _is_attempt_expired(attempt, quiz) -> bool:
#     """Kiểm tra xem attempt này đã quá hạn giờ làm bài chưa"""
#     if not quiz.time_limit_minutes:
#         return False # Không giới hạn thời gian
        
#     time_limit_seconds = quiz.time_limit_minutes * 60
#     elapsed = (timezone.now() - attempt.started_at).total_seconds()
    
#     return elapsed > time_limit_seconds


# ==========================================
# PUBLIC INTERFACE (START)
# ==========================================

@transaction.atomic
def start_or_resume_attempt(quiz_id: uuid.UUID, user, course_id: Optional[uuid.UUID] = None):
    # 1. Tìm bài đang làm dở
    attempt = QuizAttempt.objects.filter(
        user=user, 
        quiz_id=quiz_id, 
        status='in_progress'
    ).first()

    if not attempt:
        # 2. Nếu không có, tạo mới (New Attempt)
        quiz = Quiz.objects.get(id=quiz_id)

        enrollment = None
        if course_id:
            # Nếu có course_id, tìm enrollment tương ứng để link vào
            enrollment = Enrollment.objects.filter(
                user=user, 
                course_id=course_id
            ).first()
        else:
            # (Optional) Nếu không gửi course_id, có thể thử tìm enrollment gần nhất
            # chứa quiz này (dùng magic query của bạn) để auto-link.
            pass

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
            enrollment=enrollment,
            questions_order=[str(uid) for uid in selected_ids], # Lưu cứng thứ tự
            attempt_mode=quiz.mode
        )
    
    return QuizAttemptDomain.from_model(attempt)


# ==========================================
# PUBLIC INTERFACE (SUBMIT)
# ==========================================

@transaction.atomic
def finish_quiz_attempt(attempt_id: uuid.UUID, user) -> QuizAttemptDomain:
    # 1. Validate Attempt
    try:
        attempt = QuizAttempt.objects.select_related('quiz').get(id=attempt_id, user=user)
    except QuizAttempt.DoesNotExist:
        raise DomainError("Không tìm thấy bài làm.")

    # Idempotency: Nếu đã nộp rồi thì trả về kết quả cũ luôn, không chấm lại
    if attempt.status == 'submitted':
        # Load answers kèm question để tránh N+1
        answers = list(attempt.answers.select_related('question').all())
        
        # Sắp xếp lại answers theo đúng thứ tự đề thi (questions_order)
        ans_map = {a.question_id: a for a in answers}
        ordered_answers = []
        for q_id_str in attempt.questions_order:
            qid = uuid.UUID(q_id_str)
            if qid in ans_map:
                ordered_answers.append(ans_map[qid])
        
        # Gán vào cache để from_model sử dụng
        attempt._cached_answers = ordered_answers
        return QuizAttemptDomain.from_model(attempt)

    # 2. --- BATCH GRADING (Chấm điểm hàng loạt) ---
    # Lấy danh sách ID câu hỏi trong đề thi này (theo thứ tự đã random)
    question_ids = attempt.questions_order 
    
    # Lấy tất cả câu trả lời user đã lưu (Draft hoặc đã Submit lẻ)
    # Dùng in_bulk để map ID -> Object cho nhanh
    saved_answers = QuestionAnswer.objects.filter(attempt=attempt).in_bulk(field_name='question_id')
    
    total_score = 0.0
    total_max_score = 0.0 # Tính tổng điểm trần của đề thi

    # Duyệt sơ bộ để tính tổng điểm đã có và tìm câu cần chấm
    # Lưu ý: Vẫn cần loop qua all question_ids để tính total_max_score chính xác
    # (Vì có thể user chưa hề tạo record QuestionAnswer cho câu đó)
    
    # Lấy toàn bộ Question Info (Score, Type...) để tính Max Score
    # Đoạn này không né được query Question, nhưng nhẹ vì chỉ lấy field cơ bản
    all_questions = Question.objects.filter(id__in=[uuid.UUID(i) for i in question_ids]).in_bulk()

    answers_to_update = []
    answers_to_create = []

    final_processed_answers = []

    for q_id_str in question_ids:
        q_uuid = uuid.UUID(q_id_str)
        question = all_questions.get(q_uuid)
        
        if not question: continue # Edge case: Câu hỏi bị xóa khỏi DB

        q_max = getattr(question, 'score', 1.0)
        total_max_score += q_max

        answer_obj = saved_answers.get(q_uuid)

        # === LOGIC QUAN TRỌNG NHẤT Ở ĐÂY ===
        if answer_obj and answer_obj.is_graded:
            # CASE A: Đã chấm rồi (Submit từng câu) -> Tin tưởng DB
            total_score += answer_obj.score
            final_processed_answers.append(answer_obj)
        
        else:
            # CASE B: Chưa chấm (Draft) HOẶC Chưa làm (None)
            score = 0.0
            is_correct = False
            feedback = "Chưa trả lời"
            
            # Nếu có bản nháp -> Chấm bản nháp
            if answer_obj: 
                score, is_correct, feedback = evaluate_answer(question, answer_obj.answer_data)
                
                # Update vào list để bulk update sau
                answer_obj.score = score
                answer_obj.is_correct = is_correct
                answer_obj.feedback = feedback
                answer_obj.is_graded = True # <--- Chốt sổ
                answers_to_update.append(answer_obj)
                final_processed_answers.append(answer_obj)
            
            # Nếu chưa từng đụng vào -> Tạo record 0 điểm
            else:
                new_ans = QuestionAnswer(
                    attempt=attempt,
                    question=question,
                    question_type=question.type,
                    answer_data={},
                    score=0.0,
                    is_correct=False,
                    is_graded=True, # <--- Chốt sổ
                    feedback="Bạn chưa trả lời câu này."
                )
                answers_to_create.append(new_ans)
                final_processed_answers.append(new_ans)
            
            total_score += score

    # 3. Bulk Update/Create (Chỉ tác động những câu draft/new)
    if answers_to_update:
        QuestionAnswer.objects.bulk_update(answers_to_update, ['score', 'is_correct', 'feedback', 'is_graded'])
    
    if answers_to_create:
        QuestionAnswer.objects.bulk_create(answers_to_create)

    # 3. --- TÍNH TOÁN KẾT QUẢ CUỐI CÙNG ---
    # Logic Pass/Fail
    # Mặc định pass_score của quiz là % (VD: 0.8 = 80%) hoặc điểm số tuyệt đối.
    # Ở đây giả sử pass_score là điểm số tuyệt đối (VD: 5/10).
    pass_threshold = attempt.quiz.pass_score or (total_max_score * 0.5) # Default 50%

    # 4. Update QuizAttempt
    attempt.score = total_score
    attempt.max_score = total_max_score
    attempt.is_passed = (total_score >= pass_threshold)
    attempt.status = 'submitted'
    attempt.time_submitted = timezone.now()
    attempt.save()

    # 5. --- ATTACH & RETURN ---
    # Trick: Gắn list answers vào object để lớp trên dùng luôn, khỏi query
    # Lưu ý: Sắp xếp lại theo đúng order của đề thi
    answer_map = {a.question_id: a for a in final_processed_answers}
    ordered_answers = []
    for q_id_str in attempt.questions_order:
        qid = uuid.UUID(q_id_str)
        if qid in answer_map:
            ordered_answers.append(answer_map[qid])
            
    attempt._cached_answers = ordered_answers

    # 6. (Optional) Trigger Update Course Progress
    # update_enrollment_progress(attempt.enrollment)

    return QuizAttemptDomain.from_model(attempt)


# ==========================================
# PUBLIC INTERFACE (REGRADE) - INSTRUCTOR
# ==========================================

@transaction.atomic
def regrade_quiz_attempt(attempt_id: uuid.UUID) -> QuizAttemptDomain:
    """
    ADMIN/INSTRUCTOR TOOL:
    Cưỡng ép chấm lại toàn bộ bài làm dựa trên cấu hình câu hỏi HIỆN TẠI.
    Dùng khi giáo viên sửa đáp án sai sau khi học sinh đã nộp bài.
    """
    try:
        attempt = QuizAttempt.objects.select_related('quiz').get(id=attempt_id)
    except QuizAttempt.DoesNotExist:
        raise DomainError("Không tìm thấy bài làm.")

    # Lấy danh sách câu hỏi và câu trả lời
    question_ids = attempt.questions_order
    
    # Map Question ID -> Answer Object
    saved_answers = QuestionAnswer.objects.filter(attempt=attempt).in_bulk(field_name='question_id')
    
    # Map Question ID -> Question Object (Dữ liệu MỚI NHẤT từ DB)
    q_uuids = [uuid.UUID(q_id) for q_id in question_ids]
    questions_map = Question.objects.filter(id__in=q_uuids).in_bulk()

    total_score = 0.0
    total_max_score = 0.0
    
    answers_to_update = []

    for q_id_uuid, question in questions_map.items():
        # 1. Tính lại Max Score (đề phòng giáo viên sửa thang điểm)
        q_max = getattr(question, 'score', 1.0)
        total_max_score += q_max

        answer_obj = saved_answers.get(q_id_uuid)

        if answer_obj:
            # --- FORCE RE-EVALUATE ---
            # Luôn luôn chấm lại, không quan tâm is_graded cũ
            score, is_correct, feedback = evaluate_answer(question, answer_obj.answer_data)
            
            # Chỉ update nếu có sự thay đổi (Optimization nhỏ)
            if (answer_obj.score != score or 
                answer_obj.is_correct != is_correct):
                
                answer_obj.score = score
                answer_obj.is_correct = is_correct
                answer_obj.feedback = feedback
                answer_obj.is_graded = True
                answers_to_update.append(answer_obj)
            
            total_score += score
        else:
            # Nếu user chưa làm câu này thì vẫn là 0 điểm
            pass

    # 2. Bulk Update
    if answers_to_update:
        QuestionAnswer.objects.bulk_update(answers_to_update, ['score', 'is_correct', 'feedback', 'is_graded'])

    # 3. Tính lại Pass/Fail của Attempt
    pass_threshold = attempt.quiz.pass_score or (total_max_score * 0.5)
    
    attempt.score = total_score
    attempt.max_score = total_max_score
    attempt.is_passed = (total_score >= pass_threshold)
    # Không update time_submitted vì regrade không thay đổi thời gian nộp bài
    attempt.save()

    return QuizAttemptDomain.from_model(attempt)


def regrade_all_attempts_in_quiz(quiz_id: uuid.UUID):
    """
    Chạy Batch Job để chấm lại toàn bộ bài thi của 1 Quiz.
    """
    # Lấy tất cả bài đã nộp của quiz này
    attempts = QuizAttempt.objects.filter(
        quiz_id=quiz_id, 
        status='submitted' # Chỉ chấm lại bài đã nộp
    ).values_list('id', flat=True)

    count = 0
    for attempt_id in attempts:
        try:
            regrade_quiz_attempt(attempt_id)
            count += 1
        except Exception as e:
            # Log error nhưng không dừng loop
            logger.error(f"Failed to regrade attempt {attempt_id}: {e}")

    return {"detail": f"Đã chấm lại thành công {count} bài thi."}