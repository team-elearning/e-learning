import uuid
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from typing import Optional


from content.models import ContentBlock, Lesson, Module, Enrollment
from progress.models import UserBlockProgress
from progress.domains.user_block_progress_domain import UserBlockProgressDomain
from progress.domains.resume_position_domain import ResumePositionDomain
# from progress.services.course_progress_service import handle_block_completion
from progress.services.completion_strategies import evaluate



# ==========================================
# PUBLIC INTERFACE (GET)
# ==========================================

def get_interaction_status(user, block_id: str) -> UserBlockProgressDomain:
    try:
        uuid_obj = uuid.UUID(str(block_id))
    except ValueError:
        raise ValueError("block_id không hợp lệ.")

    # 1. Lấy ContentBlock trước (Cần thiết để trả về metadata cho FE)
    # Dùng select_related nếu ContentBlock có quan hệ cha con để tối ưu
    try:
        block = ContentBlock.objects.get(id=uuid_obj)
    except ContentBlock.DoesNotExist:
        raise ValueError(f"ContentBlock {block_id} không tồn tại.")

    # 2. Lấy Progress của User
    try:
        progress = UserBlockProgress.objects.get(user=user, block_id=uuid_obj)
        # Found: Merge data
        return UserBlockProgressDomain.from_model(progress, block)
        
    except UserBlockProgress.DoesNotExist:
        # Not Found: Trả về Transient Object kèm Metadata của Block
        # FE sẽ nhận được: "User chưa học (0%), nhưng video này dài 10 phút"
        return UserBlockProgressDomain.create_transient(user, block)


# ==========================================
# PUBLIC INTERFACE (TRACK)
# ==========================================

def sync_heartbeat(user, block_id: str, data: dict) -> UserBlockProgressDomain :
    """
    Hàm này xử lý ghi nhận tiến độ từ API Heartbeat.
    """
    # 1. Validation cơ bản & Lấy ContentBlock
    try:
        block = ContentBlock.objects.select_related('lesson__module__course').get(id=block_id)
    except ContentBlock.DoesNotExist:
        raise ValueError("Block không tồn tại.")

    # 2. Tìm Enrollment (BẮT BUỘC)
    # Phải đảm bảo User đã ghi danh khóa học này mới được track
    try:
        enrollment = Enrollment.objects.get(user=user, course=block.lesson.module.course)
    except Enrollment.DoesNotExist:
        raise PermissionError("User chưa ghi danh khóa học này.")

    progress, created = UserBlockProgress.objects.get_or_create(
        user=user,
        block=block,
        enrollment=enrollment,
        defaults={'is_completed': False, 'time_spent_seconds': 0}
    )

    # 3. Xử lý Logic cộng dồn (Dùng F expression để tránh Race Condition mà không cần Lock)
    time_add = data.get('time_spent_add', 0)
    incoming_interaction = data.get('interaction_data', {})

    if time_add > 0 or incoming_interaction:
        current_data = progress.interaction_data or {}
        current_data.update(incoming_interaction)
        progress.interaction_data = current_data
    
        progress.last_accessed = timezone.now()
    
    # Cộng dồn thời gian học 
    if 0 < time_add <= 300: # Cho phép tối đa 5 phút (nếu FE gửi 60s/lần)
        progress.time_spent_seconds += F('time_spent_seconds') + time_add

    progress.save()
    
    # Refresh lại từ DB để lấy giá trị số nguyên sau khi cộng F()
    progress.refresh_from_db()

    # 5. Kiểm tra hoàn thành (Chỉ check nếu chưa xong)
    if not progress.is_completed:
        is_done = evaluate(
            block=block, 
            interaction_data=incoming_interaction,
            current_progress_seconds=progress.time_spent_seconds
        )
        
        if is_done:
            with transaction.atomic():
            # Select lại để chắc chắn chưa ai update
                locked_progress = UserBlockProgress.objects.select_for_update().get(id=progress.id)
                if not locked_progress.is_completed:
                    locked_progress.is_completed = True
                    locked_progress.completed_at = timezone.now()
                    locked_progress.save()
                    # Assign lại để trả về domain đúng
                    progress = locked_progress
            # Lưu ý: Không gọi tính toán % khóa học ở đây để tránh chậm API
    
    return UserBlockProgressDomain.from_model(progress, block)


################################################################################
################################################################################
################################################################################

def validate_completion_policy(block: ContentBlock, progress: UserBlockProgress):
    """
    Unified Validator: Kiểm tra xem user đã đủ điều kiện để 'Tick xanh' chưa.
    Logic dựa trên block.type và cấu hình trong block.payload.
    """
    # Lấy cấu hình từ payload (JSON), có default value an toàn
    payload = block.payload or {}
    criteria = payload.get('completion_criteria', {}) 
    
    # --- CASE 1: VIDEO / AUDIO ---
    if block.type in ['video', 'audio']:
        # 1. Lấy duration từ payload (System define)
        duration = payload.get('duration', 0)
        
        # Nếu data lỗi không có duration -> Fallback: Bắt buộc xem tối thiểu 30s
        if not duration:
            if progress.time_spent_seconds < 30:
                raise ValueError("Dữ liệu video chưa đầy đủ, vui lòng xem tối thiểu 30s.")
            return

        # 2. Lấy ngưỡng % yêu cầu (Default Moodle thường là xem hết, ta cho 90% là mượt)
        required_percent = criteria.get('min_percent', 90)
        required_seconds = duration * (required_percent / 100)
        
        # 3. Validation
        if progress.time_spent_seconds < required_seconds:
            missing = int(required_seconds - progress.time_spent_seconds)
            raise ValueError(
                f"Bạn mới xem {int(progress.time_spent_seconds)}s. "
                f"Cần xem {required_percent}% thời lượng (còn thiếu {missing}s)."
            )

    # --- CASE 2: READING (PDF / DOC / TEXT) ---
    elif block.type in ['pdf', 'docx', 'text', 'image']:
        # Rule: Phải ở lại trang tối thiểu X giây (Moodle gọi là "View time")
        min_seconds = criteria.get('min_view_time', 5) # Default 5s để tránh click nhầm
        
        if progress.time_spent_seconds < min_seconds:
             raise ValueError(f"Vui lòng đọc tài liệu tối thiểu {min_seconds} giây.")

    # --- CASE 3: QUIZ (Bài tập) ---
    elif block.type == 'quiz':
        # Quiz thường hoàn thành khi có điểm PASS
        # Logic này thường check score chứ không check time
        passing_score = criteria.get('passing_score', 5.0)
        current_score = progress.score or 0.0
        
        if current_score < passing_score:
            raise ValueError(f"Điểm số chưa đạt. Cần {passing_score}, hiện tại {current_score}.")

    # --- CASE DEFAULT ---
    else:
        # Với các type lạ, chỉ cần có record heartbeat là cho qua
        pass


# def mark_block_as_complete(user, data: dict) -> UserBlockProgressDomain:
#     block_id = data.get('block_id') 

#     try:
#         # Select related để lấy payload xử lý validate
#         block = ContentBlock.objects.get(id=block_id)
#         # Get progress hiện tại (đã được Heartbeat update time_spent)
#         progress = UserBlockProgress.objects.get(user=user, block=block)
#     except (ContentBlock.DoesNotExist, UserBlockProgress.DoesNotExist):
#         raise ValueError("Không tìm thấy dữ liệu học tập. Vui lòng học thử vài giây trước khi hoàn thành.")

#     # 1. Idempotency (Nếu đã xong rồi thì return luôn)
#     if progress.is_completed:
#         return UserBlockProgressDomain.from_model(progress, block)

#     # 2. GỌI HÀM VALIDATE GỘP
#     # Nếu không thỏa mãn, hàm này sẽ raise ValueError -> API trả về 400
#     validate_completion_policy(block, progress)

#     # 3. Update & Ripple Effect (Quan trọng)
#     with transaction.atomic():
#         progress.is_completed = True
#         progress.last_accessed = timezone.now()
#         progress.save()
        
#         # Kích hoạt tính toán lại tiến độ Lesson/Course
#         transaction.on_commit(
#             lambda: handle_block_completion(user, block)
#         )

#     return UserBlockProgressDomain.from_model(progress, block)


##################################################################################################################
##################################################################################################################
##################################################################################################################

# def _find_next_block_optimized(current_block):
#     """
#     Tìm block tiếp theo bằng 1 Query duy nhất dựa trên so sánh tuple (module, lesson, block).
#     Điều kiện: 
#     1. Cùng Lesson, order lớn hơn.
#     2. HOẶC Khác Lesson (nhưng cùng Module), lesson order lớn hơn.
#     3. HOẶC Khác Module, module order lớn hơn.
    
#     Tuy nhiên, query trên rất phức tạp.
#     Cách tốt nhất: Dựa trên thực tế user chỉ cần tìm 1 bài ngay sau đó.
#     Ta nên tạo một method 'get_next_in_course' trong Model ContentBlock hoặc dùng thuật toán Python.
#     """
    
#     # CÁCH 1: Nếu bạn có trường 'global_order' trong ContentBlock (Recommended)
#     # return ContentBlock.objects.filter(
#     #     lesson__module__course_id=current_block.lesson.module.course_id,
#     #     global_order__gt=current_block.global_order
#     # ).order_by('global_order').first()

#     # CÁCH 2: Python approach (Nhanh nếu Course < 500 blocks)
#     # Load tất cả ID của course theo thứ tự -> Tìm index -> Lấy index + 1
#     # Moodle dùng cách này (get_fast_modinfo) và cache lại kết quả này.
    
#     course_id = current_block.lesson.module.course_id
    
#     # Query này lấy TOÀN BỘ cấu trúc course nhưng chỉ lấy ID (Rất nhẹ)
#     all_blocks_ids = ContentBlock.objects.filter(
#         lesson__module__course_id=course_id
#     ).order_by(
#         'lesson__module__position', # Order Module
#         'lesson__position',         # Order Lesson
#         'position'                  # Order Block
#     ).values_list('id', flat=True)
    
#     # Convert list
#     ids_list = list(all_blocks_ids)
    
#     try:
#         curr_index = ids_list.index(current_block.id)
#         if curr_index + 1 < len(ids_list):
#             next_id = ids_list[curr_index + 1]
#             return ContentBlock.objects.get(id=next_id)
#     except ValueError:
#         pass
        
#     return None


# def _build_resume_domain(block, user, resume_data, is_completed):
#     # Tính toán tiến độ tổng (Aggregate)
#     # Lưu ý: Query này nên cache lại (Redis) chứ không count mỗi lần gọi
#     course_id = block.lesson.module.course_id
    
#     total_blocks = ContentBlock.objects.filter(lesson__module__course_id=course_id).count()
#     completed_blocks = UserBlockProgress.objects.filter(
#         user=user, 
#         block__lesson__module__course_id=course_id,
#         is_completed=True
#     ).count()

#     percent = 0.0
#     if total_blocks > 0:
#         percent = round((completed_blocks / total_blocks) * 100, 1)

#     return ResumePositionDomain(
#         # ... mapping fields ...
#         course_progress_percent=percent,
#         total_blocks=total_blocks,
#         completed_blocks=completed_blocks
#     )


# def _get_first_block_of_course(course_id: uuid.UUID) -> Optional[ContentBlock]:
#     """
#     Tìm ContentBlock ĐẦU TIÊN của một khóa học.
#     Logic: Tìm Module có position nhỏ nhất -> Lesson nhỏ nhất -> Block nhỏ nhất.
#     """
#     first_block = ContentBlock.objects.filter(
#         # Filter các block thuộc course này (thông qua quan hệ ngược)
#         lesson__module__course_id=course_id,
        
#         # (Quan trọng) Chỉ lấy các nội dung đã Public
#         lesson__published=True,
#         # lesson__module__published=True # Bật nếu model Module có field published
#     ).select_related(
#         'lesson', 'lesson__module' # Join sẵn để tránh N+1 khi convert sang Domain sau này
#     ).order_by(
#         # Sắp xếp phân cấp: Module -> Lesson -> Block
#         'lesson__module__position', # Module đầu tiên
#         'lesson__position',         # Lesson đầu tiên trong module đó
#         'position'                  # Block đầu tiên trong lesson đó
#     ).first()

#     return first_block


# def get_course_resume_position(user, course_id: str) -> Optional[ResumePositionDomain]:
#     """
#     Logic tìm điểm 'Resume'.
#     Input: user, course_id
#     Output: ResumePositionDomain hoặc None (nếu course rỗng)
#     """
#     # 1. Validate input
#     try:
#         course_uuid = uuid.UUID(str(course_id))
#     except ValueError:
#         raise ValueError("Course ID không hợp lệ.")

#     # 2. Tìm lịch sử học tập gần nhất (Last Access)
#     # Query: Tìm record UserBlockProgress thuộc course này, có last_accessed mới nhất
#     last_progress = UserBlockProgress.objects.filter(
#         user=user,
#         block__lesson__module__course_id=course_uuid
#     ).select_related(
#         'block', 'block__lesson', 'block__lesson__module' # Join để lấy ID lesson/module tránh N+1
#     ).order_by('-last_accessed').first()

#     target_block = None
#     resume_data = {}
#     is_completed = False

#     # CASE A: Chưa học gì -> Lấy bài đầu tiên
#     if not last_progress:
#         target_block = _get_first_block_of_course(course_uuid)
#         if target_block:
#              return ResumePositionDomain.from_first_block(target_block, user.id)
#         return None
    
#     # CASE B: Đã có lịch sử -> Check xem đã xong chưa?
#     current_block = last_progress.block
    
#     target_block = current_block
#     resume_data = last_progress.resume_data
#     is_completed = last_progress.is_completed

#     # [MOODLE STYLE LOGIC]
#     # Chỉ Auto-advance nếu block cũ là dạng "Passive" (Video/Text) đã hoàn thành.
#     # Nếu block cũ là Quiz/Exercise, dù hoàn thành cũng KHÔNG tự next (để user xem điểm).
    
#     should_auto_advance = False
    
#     if is_completed:
#         # Nếu là Video -> Auto next cho mượt
#         if current_block.type in ['video', 'audio']:
#             should_auto_advance = True
        
#         # Nếu là Quiz -> Không next (để user review kết quả)
#         elif current_block.type in ['quiz', 'exercise']:
#             should_auto_advance = False
            
#     if should_auto_advance:
#         # Dùng hàm optimized ở trên
#         next_block = _find_next_block_optimized(current_block)
#         if next_block:
#             target_block = next_block
#             resume_data = {}
#             is_completed = False

#     # Return Domain
#     return _build_resume_domain(target_block, user, resume_data, is_completed)