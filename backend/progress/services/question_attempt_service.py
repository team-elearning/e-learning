import uuid
from typing import Dict, Any, List
from django.db import transaction
from django.conf import settings
from django.db.models import Case, When, Prefetch
from django.utils import timezone
import random

from core.exceptions import DomainError
from core.services.media_service import recursive_inject_cdn_url
from quiz.models import Quiz, Question
from progress.models import QuizAttempt, QuestionAnswer
from progress.domains.question_content_domain import QuestionContentDomain
from progress.domains.question_result_domain import QuizItemResultDomain



# ==========================================
# PUBLIC INTERFACE (HELPER)
# ==========================================

def evaluate_answer(question: Question, user_answer_data: Dict[str, Any]) -> tuple[float, bool, str]:
    """
    Core Logic chấm điểm.
    Returns: (score, is_correct, feedback)
    """
    # Lấy điểm tối đa của câu hỏi (Giả sử bạn có field score trên model Question, nếu không thì default 1)
    max_score = getattr(question, 'score', 1.0)
    
    # Lấy cấu hình đáp án đúng từ DB
    payload = question.answer_payload
    explanation = payload.get('explanation', '')

    score = 0.0
    is_correct = False
    feedback = ""

    # --- CASE 1: Single Choice / True False ---
    if question.type in ['multiple_choice_single', 'true_false']:
        # User gửi: {'selected_ids': ['uuid-A']} hoặc {'selected_id': 'uuid-A'}
        # Chuẩn hóa input list về string
        u_sel = user_answer_data.get('selected_ids', [])
        user_val = u_sel[0] if isinstance(u_sel, list) and u_sel else user_answer_data.get('selected_id')
        
        correct_val = payload.get('correct_ids')

        if str(user_val) == str(correct_val):
            score = max_score
            is_correct = True
            feedback = "Chính xác!"
        else:
            feedback = "Sai rồi."

    # --- CASE 2: Multi Choice (Có điểm thành phần) ---
    elif question.type == 'multiple_choice_multi':
        user_ids = set(str(x) for x in user_answer_data.get('selected_ids', []))
        correct_ids = set(str(x) for x in payload.get('correct_ids', []))
        
        if user_ids == correct_ids:
            score = max_score
            is_correct = True
            feedback = "Chính xác hoàn toàn!"
        else:
            # Logic Moodle: Chọn sai bị trừ điểm, hoặc chỉ tính % câu đúng.
            # Ở đây dùng logic an toàn: Đúng hết mới được điểm (Strict)
            # Hoặc Partial:
            if payload.get('allow_partial', False) and correct_ids:
                # Số ý đúng user chọn được
                correct_hits = len(user_ids & correct_ids)
                # Số ý sai user chọn nhầm
                wrong_hits = len(user_ids - correct_ids)
                
                # Điểm = (Đúng - Sai) / Tổng số đúng
                ratio = max(0, (correct_hits - wrong_hits) / len(correct_ids))
                score = round(ratio * max_score, 2)
                is_correct = (ratio == 1.0)
                feedback = f"Bạn trả lời đúng một phần ({int(ratio*100)}%)."
            else:
                feedback = "Chưa chính xác."

    # --- CASE 3: Fill in blank / Short Answer ---
    elif question.type in ['short_answer', 'fill_in_the_blank']:
        user_text = str(user_answer_data.get('text', '')).strip()
        accepted_texts = payload.get('accepted_texts', [])
        
        # Moodle logic: Case sensitivity settings
        if not payload.get('case_sensitive', False):
            user_text = user_text.lower()
            accepted_texts = [t.lower() for t in accepted_texts]
            
        if user_text in accepted_texts:
            score = max_score
            is_correct = True
            feedback = "Chính xác!"
        else:
            feedback = "Sai rồi."

    # --- CASE 4: Matching / Ordering ---
    elif question.type == 'matching':
        # Matching thì nên tính partial credit
        correct_map = payload.get('matches', {}) # {"A": "1", "B": "2"}
        user_map = user_answer_data.get('matches', {}) # {"A": "1", "B": "3"}
        
        total_pairs = len(correct_map)
        if total_pairs > 0:
            correct_count = 0
            for k, v in correct_map.items():
                if str(user_map.get(k)) == str(v):
                    correct_count += 1
            
            score = round((correct_count / total_pairs) * max_score, 2)
            is_correct = (correct_count == total_pairs)
            feedback = f"Bạn ghép đúng {correct_count}/{total_pairs} cặp."

    # --- CASE 5: Essay (Tự luận) ---
    elif question.type == 'essay':
        # Logic: Có chữ là có điểm
        user_text = str(user_answer_data.get('text', '')).strip()
        
        if len(user_text) > 0:
            score = max_score
            is_correct = True
            feedback = "Đã ghi nhận câu trả lời."
        else:
            score = 0.0
            is_correct = False
            feedback = "Bạn chưa nhập nội dung."

    # Ghép explanation chung vào feedback
    if explanation:
        feedback += f" \nGiải thích: {explanation}"

    return score, is_correct, feedback


def get_correct_answer_for_display(question: Question) -> Dict[str, Any]:
    """
    Trả về cấu trúc đáp án đúng để Frontend hiển thị.
    Cần chạy qua recursive_inject_cdn_url để đảm bảo ảnh trong đáp án (nếu có) hiển thị được.
    """
    payload = question.answer_payload
    q_type = question.type
    
    # Data gốc từ DB
    raw_display_data = {}

    if q_type in ['multiple_choice_single']:
        raw_display_data = {
            "correct_id": payload.get('correct_id', [])
        }

    elif q_type == 'multiple_choice_multi':
        raw_display_data = {
            "correct_ids": payload.get('correct_ids', [])
        }

    elif q_type == 'true_false':
        # Ví dụ payload: { "correct_value": true }
        raw_display_data = {
            "correct_value": payload.get('correct_value')
        }

    elif q_type in ['short_answer', 'fill_in_the_blank']:
        # Chỉ hiện 1 đáp án mẫu đầu tiên
        raw_display_data = {
            "accepted_texts": payload.get('accepted_answers', []) # Map sang key FE dễ hiểu
        }

    elif q_type == 'matching':
        # Trả về cặp đúng: {"matches": {"A": "1", "B": "2"}}
        raw_display_data = {
            "matches": payload.get('matches', {})
        }
        
    elif q_type == 'ordering':
        raw_display_data = {
            "correct_order": payload.get('correct_order', [])
        }

    elif q_type == 'essay':
        # Essay không có đáp án đúng sai tuyệt đối.
        # Ta trả về hướng dẫn chấm (Rubric) hoặc bài mẫu để FE hiển thị
        raw_display_data = {
            "rubric": payload.get('grading_rubric', ''),
            "model_answer": payload.get('model_answer', '') # Nếu có bài văn mẫu
        }

    # Thêm explanation chung
    if 'explanation' in payload:
        raw_display_data['explanation'] = payload['explanation']

    # QUAN TRỌNG: Inject URL vào dữ liệu hiển thị này
    # Vì có thể explanation chứa ảnh, hoặc matches chứa ảnh
    return recursive_inject_cdn_url(raw_display_data)


# ==========================================
# PUBLIC INTERFACE (GET)
# ==========================================

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

    # Phải biến đổi toàn bộ JSON thô thành JSON có link CDN xịn ngay từ đầu.
    # Hàm này sẽ đệ quy vào cả 'options', 'image', 'text' để gắn link.
    processed_prompt = recursive_inject_cdn_url(question.prompt)

    # Lúc này các item trong list này đã có field 'url' (nếu là ảnh)
    options_with_urls = processed_prompt.get('options', ["chekc"])

    # # --- Logic Random Đáp Án (Option Shuffle) ---    
    # Để đảm bảo user F5 không bị đổi thứ tự đáp án liên tục, 
    # ta dùng seed = attempt_id + question_id
    seed_val = str(attempt.id) + str(question.id)
    random.seed(seed_val) 
    
    shuffled_options = options_with_urls.copy()
    random.shuffle(shuffled_options)

    # 2. --- LOGIC MỚI: TÌM CÂU TRẢ LỜI CŨ (RESUME) ---
    # Tìm xem user đã từng trả lời câu này chưa
    # Dùng filter().first() để tránh lỗi nếu chưa có record
    existing_answer = QuestionAnswer.objects.filter(
        attempt=attempt, 
        question=question
    ).first()

    saved_answer_data = {}
    saved_flag_status = False
    
    # Thêm 2 trường này để Frontend biết câu này đã chấm chưa
    submission_result = None

    if existing_answer:
        saved_answer_data = existing_answer.answer_data
        saved_flag_status = existing_answer.is_flagged
        
        # Nếu câu này đã được chấm (ví dụ trong mode Practice user đã bấm Submit),
        # ta cần trả về kết quả luôn để hiển thị lại (chứ user F5 xong mất màu xanh đỏ thì kì)
        # Lưu ý: Chỉ trả về kết quả nếu score hoặc feedback đã có giá trị (tức là đã submit thật)
        if existing_answer.feedback or existing_answer.score > 0 or existing_answer.is_correct:
             
             # Logic lấy đáp án đúng (chỉ hiện nếu là Practice hoặc Exam cho phép review)
             correct_display = None
             if attempt.attempt_mode in ['practice', 'quiz']:
                 correct_display = get_correct_answer_for_display(question)
                 
             submission_result = {
                 "is_correct": existing_answer.is_correct,
                 "score": existing_answer.score,
                 "feedback": existing_answer.feedback,
                 "correct_answer": correct_display
             }

    return QuestionContentDomain(
        id=question.id,
        type=question.type,
        prompt_text=processed_prompt.get('text', ''),
        prompt_image=processed_prompt.get('image', None),
        options=shuffled_options,
        current_answer=saved_answer_data, 
        is_flagged=saved_flag_status,
        submission_result=submission_result
    )


# ==========================================
# PUBLIC INTERFACE (DRAFT)
# ==========================================

@transaction.atomic
def save_question_draft(
    attempt_id: uuid.UUID, 
    question_id: uuid.UUID,
    submission_data: dict, # Chứa answer_data
    user
) -> bool:
    """
    AUTOSAVE: Chỉ lưu trạng thái trả lời của user, KHÔNG chấm điểm.
    Dùng khi user tích vào ô checkbox, hoặc gõ text (debounce).
    """
    # 1. Validate Attempt (Giống hệt submit)
    try:
        attempt = QuizAttempt.objects.get(id=attempt_id, user=user)
    except QuizAttempt.DoesNotExist:
        raise DomainError("Không tìm thấy bài làm.")

    if attempt.status != 'in_progress':
        raise DomainError("Bài làm đã đóng, không thể lưu nháp.")

    if str(question_id) not in attempt.questions_order:
        raise DomainError("Câu hỏi không thuộc bài làm này.")

    # 2. Check trạng thái câu hỏi hiện tại (Logic mới thêm)
    # Tìm xem câu này đã từng được trả lời chưa
    existing_ans = QuestionAnswer.objects.filter(
        attempt=attempt, 
        question_id=question_id
    ).first()

    # NẾU ĐÃ CHẤM RỒI -> CHẶN LUÔN
    if existing_ans and existing_ans.is_graded:
        raise DomainError("Câu hỏi này đã nộp, không thể sửa lại.")

    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        raise DomainError("Câu hỏi không tồn tại.")

    # 2. Lưu nháp (Update or Create)
    # Lưu ý: Không set score, không set is_correct, không set feedback
    QuestionAnswer.objects.update_or_create(
        attempt=attempt,
        question=question,
        defaults={
            'question_type': question.type,
            'answer_data': submission_data['answer_data'],
            # Giữ nguyên các trường chấm điểm là mặc định (hoặc 0)
            # Nếu bản ghi đã tồn tại và đã được chấm điểm trước đó (trong practice mode),
            # việc user sửa lại đáp án sẽ làm kết quả cũ không còn giá trị -> Có thể reset score về 0.
            'score': 0.0,
            'is_graded': False,
            'is_correct': False,
            'feedback': None # Xóa feedback cũ nếu có
        }
    )
    
    return True


# ==========================================
# PUBLIC INTERFACE (SUBMIT)
# ==========================================

@transaction.atomic
def submit_question(
    attempt_id: uuid.UUID, 
    question_id: uuid.UUID,
    submission_data: dict, # Chứa answer_data
    user
) -> QuizItemResultDomain:
    
    # 1. Validate Attempt
    try:
        attempt = QuizAttempt.objects.select_related('quiz').get(id=attempt_id, user=user)
    except QuizAttempt.DoesNotExist:
        raise DomainError("Không tìm thấy bài làm.")

    if attempt.status != 'in_progress':
        raise DomainError("Bài làm đã kết thúc, không thể nộp thêm.")

    if str(question_id) not in attempt.questions_order:
        raise DomainError("Câu hỏi không thuộc bài làm này.")
    
    # Check trạng thái câu hỏi (Logic mới thêm)
    existing_ans = QuestionAnswer.objects.filter(
        attempt=attempt, 
        question_id=question_id
    ).select_related('question').first() # select_related để tối ưu nếu dùng lại

    # NẾU ĐÃ CHẤM RỒI -> CHẶN NỘP LẠI
    if existing_ans and existing_ans.is_graded:
        # Tùy chọn: Có thể trả về kết quả cũ thay vì raise Error (Idempotency)
        # Nhưng theo yêu cầu chặt chẽ, ta raise Error
        raise DomainError("Bạn đã nộp câu hỏi này rồi.")

    # 2. Lấy câu hỏi gốc
    if existing_ans:
        question = existing_ans.question
    else:
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            raise DomainError("Câu hỏi không tồn tại.")

    # 3. --- CHẤM ĐIỂM (GRADING LOGIC) ---
    # Tách logic chấm điểm ra hàm riêng để code gọn và dễ mở rộng
    user_answer = submission_data['answer_data']
    score_achieved, is_correct, system_feedback = evaluate_answer(question, user_answer)

    # 4. Lưu/Cập nhật vào bảng QuestionAnswer
    # Dùng update_or_create vì user có thể chọn lại đáp án nhiều lần trước khi nộp bài
    ans_obj, created = QuestionAnswer.objects.update_or_create(
        attempt=attempt,
        question=question,
        defaults={
            'question_type': question.type,
            'answer_data': user_answer,
            'is_flagged': False, # Reset flag nếu user đã nộp
            'score': score_achieved,
            'is_graded': True,
            'is_correct': is_correct,
            'feedback': system_feedback 
        }
    )

    # Optimization: Gán ngược lại question object vào ans_obj để from_orm không phải query lại
    ans_obj.question = question

    # 5. Determine Visibility
    # Logic: Practice/Quiz -> Hiện đáp án ngay. Exam -> Ẩn.
    should_show_answer = attempt.attempt_mode in ['practice', 'quiz']

    # 6. Return Domain
    return QuizItemResultDomain.from_model(
        ans=ans_obj, 
        show_correct_answer=should_show_answer
    )