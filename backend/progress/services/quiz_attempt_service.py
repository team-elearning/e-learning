import random
import uuid
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

from quiz.models import Quiz
from progress.models import QuizAttempt
from progress.domains.quiz_attempt_domain import QuizAttemptDomain



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