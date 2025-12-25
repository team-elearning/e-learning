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
from progress.domains.question_result_domain import QuizItemResultDomain
from progress.services.question_attempt_service import evaluate_answer
from progress.tasks import _safe_trigger_async_task
from analytics.services.log_service import record_activity



logger = logging.getLogger(__name__)

# ==========================================
# PUBLIC INTERFACE (HELPER)
# ==========================================

def calculate_grades(attempt, all_questions_map, saved_answers_map):
    """
    Hàm thuần túy (Pure Function): Tính toán điểm số trong RAM.
    Trả về: (total_score, max_score, answers_to_update, answers_to_create, processed_list)
    """
    total_score = 0.0
    total_max_score = 0.0
    
    answers_to_update = []
    answers_to_create = []
    final_processed_list = []

    # Duyệt theo thứ tự đề thi (questions_order)
    for q_id_str in attempt.questions_order:
        q_uuid = uuid.UUID(q_id_str)
        question = all_questions_map.get(q_uuid)
        
        if not question: continue 

        q_max = getattr(question, 'score', 1.0)
        total_max_score += q_max

        # Lấy câu trả lời user đã lưu (nếu có)
        answer_obj = saved_answers_map.get(q_uuid)

        # Logic chấm điểm
        if answer_obj and answer_obj.is_graded:
            # Case 1: Đã chấm rồi (VD: user submit lẻ tẻ trước đó)
            total_score += answer_obj.score
            final_processed_list.append(answer_obj)
        else:
            # Case 2: Cần chấm (Draft hoặc chưa làm)
            # Hàm evaluate_answer tách riêng để xử lý logic đúng/sai từng loại câu hỏi
            user_data = answer_obj.answer_data if answer_obj else {}
            score, is_correct, feedback = evaluate_answer(question, user_data)
            
            if answer_obj:
                # Update Draft
                answer_obj.score = score
                answer_obj.is_correct = is_correct
                answer_obj.feedback = feedback
                answer_obj.is_graded = True
                answers_to_update.append(answer_obj)
                final_processed_list.append(answer_obj)
            else:
                # Create New (Skipped question)
                new_ans = QuestionAnswer(
                    attempt=attempt,
                    question=question,
                    question_id=question.id, # Gán ID trực tiếp để tối ưu
                    question_type=question.type,
                    answer_data={}, # Empty answer
                    score=0.0,
                    is_correct=False,
                    is_graded=True,
                    feedback="Chưa trả lời"
                )
                answers_to_create.append(new_ans)
                final_processed_list.append(new_ans)
            
            total_score += score

    return total_score, total_max_score, answers_to_update, answers_to_create, final_processed_list


def _build_return_domain(attempt) -> QuizAttemptDomain:
    """Helper map Model -> Domain"""
    # Logic lấy cached answers
    answers = getattr(attempt, '_cached_graded_answers', None)
    if not answers:
        answers = list(attempt.answers.select_related('question').all())
    
    # 2. [OPTIMIZATION] Pre-calculate Option Map
    # Tạo Map: { question_id: { 'opt_id': 'opt_text' } }
    # Giúp Domain tra cứu text đáp án (A -> Hà Nội) cực nhanh O(1)
    global_lookup = {}

    # Sort answers theo đúng thứ tự đề thi (questions_order)
    # Tạo map {question_id: answer_obj}
    ans_map = {str(a.question_id): a for a in answers}

    sorted_items = []

    for q_id_str in attempt.questions_order:
        ans = ans_map.get(q_id_str)
        if not ans: continue # Skip nếu lỗi data

        # Build Option Map cho câu hỏi này
        if q_id_str not in global_lookup:
            opts = ans.question.prompt.get('options', [])
            global_lookup[q_id_str] = {
                str(o['id']): o['text'] for o in opts if 'id' in o and 'text' in o
            }
        
        # Gọi Domain Factory (Truyền map vào)
        item_domain = QuizItemResultDomain.from_model(
            ans, 
            lookup_map=global_lookup[q_id_str]
        )
        sorted_items.append(item_domain)
    
    return QuizAttemptDomain.from_model(attempt, items=sorted_items)

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
    # 1. ACQUIRE ROW LOCK (Khóa dòng)
    # Câu lệnh SQL thực tế nó chạy: 
    # SELECT * FROM progress_quizattempt WHERE id = '...' AND user_id = '...' FOR UPDATE;
    # => Chỉ khóa đúng 1 dòng này. Các user khác không ảnh hưởng.
    try:
        attempt = QuizAttempt.objects.select_for_update(of=('self',))\
            .select_related('quiz')\
            .get(id=attempt_id, user=user)
    except QuizAttempt.DoesNotExist:
        raise DomainError("Không tìm thấy bài làm.")

    # Idempotency: Nếu đã nộp rồi thì trả về kết quả cũ luôn, không chấm lại
    if attempt.status == 'submitted':
        return _build_return_domain(attempt)

    # 2. --- BATCH GRADING (Chấm điểm hàng loạt) ---
    # Lấy danh sách ID câu hỏi trong đề thi này (theo thứ tự đã random)
    question_ids = [uuid.UUID(i) for i in attempt.questions_order]
    all_questions_map = Question.objects.in_bulk(question_ids)
    
    # Lấy tất cả câu trả lời user đã lưu (Draft hoặc đã Submit lẻ)
    # Dùng in_bulk để map ID -> Object cho nhanh
    saved_answers_qs = QuestionAnswer.objects.filter(attempt=attempt)
    saved_answers = {a.question_id: a for a in saved_answers_qs}
    
    total_score, max_score, to_update, to_create, final_list = calculate_grades(
        attempt, all_questions_map, saved_answers
    )

    # 3. Bulk Update/Create (Chỉ tác động những câu draft/new)
    if to_update:
        QuestionAnswer.objects.bulk_update(
            to_update, ['score', 'is_correct', 'feedback', 'is_graded']
        )
    
    if to_create:
        QuestionAnswer.objects.bulk_create(to_create)

    # 4. Update QuizAttempt
    attempt.score = total_score
    attempt.max_score = max_score

    pass_threshold = attempt.quiz.pass_score or (max_score * 0.5)
    attempt.is_passed = (total_score >= pass_threshold)
    print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh", attempt.is_passed)

    attempt.status = 'submitted'
    attempt.time_submitted = timezone.now()
    attempt.save()

    # ========================================================
    # 5. [FIX] GHI LOG NGAY TẠI ĐÂY (Để lấy được IP/UA chuẩn)
    # ========================================================
    record_activity(user, {
        'action': 'QUIZ_SUBMIT',
        'entity_type': 'quiz',
        'entity_id': str(attempt.quiz_id),
        'is_critical': True, # Để ghi sync & update streak ngay
        'payload': {
            'score': attempt.score,
            'passed': attempt.is_passed
        }
    })

    # 6. Trigger Background Tasks (Fire & Forget)
    # Đẩy việc tính % khóa học, lưu analytics, gửi mail ra worker
    c_id = str(attempt.enrollment.course_id) if attempt.enrollment else None
    transaction.on_commit(lambda: _safe_trigger_async_task(
        attempt_id=str(attempt.id),
        user_id=str(user.id),
        course_id=c_id
    ))

    # 7. Construct Result Domain
    # Attach list question đã chấm vào attempt để helper function dùng luôn
    # Cần map lại object question vào answer để domain lấy được text câu hỏi
    for ans in final_list:
        if not hasattr(ans, 'question'): 
             ans.question = all_questions_map.get(ans.question_id)
             
    attempt._cached_graded_answers = final_list
    return _build_return_domain(attempt)


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