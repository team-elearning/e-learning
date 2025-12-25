import uuid
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from typing import Optional, List


from content.models import ContentBlock, Lesson, Module, Enrollment
from progress.models import UserBlockProgress, LessonCompletion, ModuleCompletion, QuizAttempt
from progress.domains.user_block_progress_domain import UserBlockProgressDomain
from progress.domains.reset_progress_result_domain import ResetProgressResultDomain
from progress.domains.course_progress_domain import CourseProgressDomain
from progress.domains.course_card_domain import CourseCardDomain
from progress.domains.resume_point_domain import ResumePointDomain
from progress.tasks import calculate_aggregation
from analytics.services.log_service import record_activity



# ==========================================
# PUBLIC INTERFACE (HELPER)
# ==========================================

def evaluate(block: ContentBlock, interaction_data: dict, current_progress_seconds: int) -> bool:
    block_type = block.type
    payload = block.payload or {}

    # --- LOGIC 1: VIDEO (Xong khi xem > 90%) ---
    if block_type == 'video':
        duration = block.duration

        if duration == 0:
            payload = block.payload or {}
            duration = payload.get('duration', 0)

        if duration == 0: 
            return True # Safe-guard: Video lỗi duration thì cho qua
        
        # Cách 1: Dựa vào timestamp hiện tại (Client gửi lên)
        current_time = interaction_data.get('video_timestamp', 0)
        if current_time / duration >= 0.9:
            return True
            
        # Cách 2: Dựa vào tổng thời gian user đã ở lại trang (Server tính)
        # if current_progress_seconds / duration >= 0.9:
        #     return True
        
        return False

    # --- LOGIC 2: QUIZ (Xong khi submit và pass - Xử lý ở API khác, ko phải heartbeat) ---
    elif block_type == 'quiz':
        # Heartbeat chỉ track thời gian làm bài, không bao giờ đánh dấu hoàn thành Quiz
        return False

    # --- LOGIC 3: TEXT/PDF (Xong khi scroll cuối hoặc ở đủ lâu) ---
    elif block_type in ['rich_text', 'pdf', 'docx']:
        # Client gửi flag 'read_complete' khi scroll xuống cuối
        if interaction_data.get('read_complete') is True:
            return True
        
        # Hoặc ở lại trang đủ tối thiểu 10 giây
        min_read_time = payload.get('min_read_seconds', 10)
        if current_progress_seconds >= min_read_time:
            return True
            
        return False

    return False


# ==========================================
# PUBLIC INTERFACE (GET BLOCK INTERACTION)
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
# PUBLIC INTERFACE (GET COURSE PROGRESS)
# ==========================================

def get_course_progress(user, course_id: str) -> CourseProgressDomain:
    """
    Lấy tiến độ tổng quan của 1 khóa học.
    """
    try:
        course_uuid = uuid.UUID(str(course_id))
    except ValueError:
        raise ValueError("course_id không hợp lệ.")

    # 1. Tìm Enrollment
    try:
        # select_related không cần thiết lắm nếu chỉ lấy field của enrollment, 
        # nhưng nếu domain cần title khóa học thì nên thêm.
        enrollment = Enrollment.objects.get(user=user, course_id=course_uuid)
    except Enrollment.DoesNotExist:
        # Tùy nghiệp vụ: 
        # - Nếu chưa enroll thì trả về lỗi 404 (Không tìm thấy tiến độ)
        # - Hoặc trả về object rỗng 0% (nếu cho phép xem trước)
        raise PermissionError("User chưa ghi danh khóa học này.")

    # 2. Return Domain
    return CourseProgressDomain.from_model(enrollment)


# ==========================================
# PUBLIC INTERFACE (GET LEARNING COURSE)
# ==========================================

def get_my_learning_hub(user_id: str) -> List[CourseCardDomain]:
    """
    Lấy danh sách khóa học của tôi (My Learning).
    Logic tham khảo Moodle:
    - Phân biệt khóa "Chưa học" và "Đang học".
    - Nút Resume trỏ đúng bài đang dở hoặc bài đầu tiên.
    """
    
    # 1. Query Enrollments (Active & In-Progress)
    # Sử dụng select_related để lấy thông tin Course và Owner trong 1 query
    enrollments = Enrollment.objects.filter(
        user_id=user_id, 
        is_completed=False
    ).select_related(
        'course', 
        'course__owner',
        'current_block',         # Eager load bài đang học dở
        'current_block__lesson'  # Eager load tên bài học
    ).order_by('-last_accessed_at')

    learning_paths = []

    for enroll in enrollments:
        resume_info = None

        if enroll.current_block:
            resume_info = ResumePointDomain(
                block_id=str(enroll.current_block.id),
                lesson_title=enroll.current_block.lesson.title,
                block_type=enroll.current_block.type,
                is_start=False
            )
        
        # 2. Nếu chưa có (Cold Start), ta để None.
        # Frontend sẽ check: Nếu resume_info == None -> Hiện nút "Start Course".
        # Khi bấm Start -> Gọi API Player -> Player sẽ tự tìm bài đầu tiên (create_transient).
        # Cách này giúp Dashboard load siêu nhanh vì không phải đi tìm bài đầu tiên cho từng khóa.
        
        learning_paths.append(CourseCardDomain(
            course_id=str(enroll.course.id),
            title=enroll.course.title,
            thumbnail=enroll.course.thumbnail.url if enroll.course.thumbnail else None,
            owner_name=getattr(enroll.course.owner, 'email', 'Instructor'),
            
            percent_completed=enroll.percent_completed,
            is_completed=enroll.is_completed,
            last_accessed_at=enroll.last_accessed_at,
            
            display_status='not_started' if not resume_info else 'in_progress',
            resume_point=resume_info
        ))
     
    return learning_paths


# ==========================================
# GET RESUME LEARNING
# ==========================================

def get_resume_state(user, course_id: str) -> UserBlockProgressDomain:
    """
    Logic:
    1. Tìm bài học user học gần nhất (last_accessed).
    2. Nếu chưa học bài nào -> Tìm bài học đầu tiên của khóa.
    3. Trả về Domain Object (Real hoặc Transient).
    """
    try:
        course_uuid = uuid.UUID(str(course_id))
    except ValueError:
        raise ValueError("course_id không hợp lệ.")

    # 1. Tìm Enrollment
    try:
        enrollment = Enrollment.objects.select_related('current_block').get(
            user=user, course_id=course_uuid
        )
    except Enrollment.DoesNotExist:
            raise PermissionError("User chưa ghi danh khóa học này.")

    # 2. Xác định Block cần học
    target_block = None

    # Ưu tiên 1: Lấy từ cache enrollment (cái vừa thêm)
    if enrollment.current_block:
        target_block = enrollment.current_block
        
        # Lấy Progress chi tiết từ bảng UserBlockProgress
        # (Vì Enrollment chỉ lưu ID, không lưu timestamp giây thứ mấy)
        progress = UserBlockProgress.objects.filter(
            user=user, block=target_block
        ).first()
        
        if progress:
            return UserBlockProgressDomain.from_model(progress, target_block)

    # Ưu tiên 2: Cold Start (Chưa học bài nào hoặc data bị lệch)
    # Tìm bài đầu tiên
    if not target_block:
        target_block = ContentBlock.objects.filter(
            lesson__module__course_id=course_uuid
        ).select_related('lesson').order_by(
            'lesson__module__position', 'lesson__position', 'position'
        ).first()

    if not target_block:
        raise ValueError("Khóa học chưa có nội dung nào để học.")

    # Trả về object tạm (chưa lưu DB) để FE biết bài nào cần play
    return UserBlockProgressDomain.create_transient(user, target_block)


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
        enrollment = Enrollment.objects.get(user=user, course=block.lesson.module.course)
        course = block.lesson.module.course

    except ContentBlock.DoesNotExist:
        raise ValueError("Block không tồn tại.")
    
    except Enrollment.DoesNotExist:
        raise PermissionError("User chưa ghi danh khóa học này.")
    
    now = timezone.now()
    
    # ---------------------------------------------------------
    # 2. TỐI ƯU POINTER (DEBOUNCE STRATEGY)
    # ---------------------------------------------------------
    # Không update timestamp liên tục mỗi 30s. Chỉ update khi:
    # A. User chuyển sang bài học khác.
    # B. User ở bài cũ nhưng đã quá 5 phút chưa update (để Dashboard biết user online).

    should_update_pointer = False

    if enrollment.current_block_id != block.id:
        enrollment.current_block = block
        should_update_pointer = True
    elif (now - enrollment.last_accessed_at).total_seconds() > 300:
        should_update_pointer = True

    if should_update_pointer:
        enrollment.last_accessed_at = now
        # Chỉ update field cần thiết
        enrollment.save(update_fields=['current_block', 'last_accessed_at'] if enrollment.current_block_id != block.id else ['last_accessed_at'])

    # ---------------------------------------------------------
    # 3. LOGIC CỘNG DỒN TRONG MEMORY (Tránh F expression)
    # ---------------------------------------------------------
    progress, created = UserBlockProgress.objects.get_or_create(
        user=user,
        block=block,
        enrollment=enrollment,
        defaults={'is_completed': False, 'time_spent_seconds': 0}
    )

    # 3. Xử lý Logic cộng dồn (Dùng F expression để tránh Race Condition mà không cần Lock)
    time_add = data.get('time_spent_add', 0)
    incoming_interaction = data.get('interaction_data', {})
    has_changes = False

    # A. Update Data
    if incoming_interaction:
        current_data = progress.interaction_data or {}
        current_data.update(incoming_interaction)
        progress.interaction_data = current_data
        has_changes = True

    # B. Update Time (Giới hạn max 5 phút để tránh hack/bug FE)
    if 0 < time_add <= 300:
        progress.time_spent_seconds += time_add 
        has_changes = True

    # ---------------------------------------------------------
    # 4. CHECK COMPLETION (In-Memory)
    # ---------------------------------------------------------
    just_completed = False

    # 5. Kiểm tra hoàn thành (Chỉ check nếu chưa xong)
    if not progress.is_completed:
        is_done = evaluate(
            block=block, 
            interaction_data=progress.interaction_data,
            current_progress_seconds=progress.time_spent_seconds
        )
        
        if is_done:
            progress.is_completed = True
            progress.completed_at = now
            progress.score = 100 # Default score
            just_completed = True
            has_changes = True

    # ---------------------------------------------------------
    # 5. SMART LOGGING & ASYNC TASKS
    # ---------------------------------------------------------
    # A. Trigger khi HOÀN THÀNH (Lesson Complete)
    if just_completed:
        # 1. Async Log
        record_activity(user, {
            'action': 'LESSON_COMPLETE',
            'entity_type': 'content_block',
            'entity_id': str(block.id),
            'course_id': str(course.id),
            'is_critical': False # Async
        })
        
        # 2. Async Aggregation (Quan trọng: Đẩy xuống background)
        transaction.on_commit(
            lambda: calculate_aggregation.delay(str(enrollment.id), str(block.lesson_id))
        )

    # B. Trigger khi HỌC ĐỦ LÂU (Learning Session)
    # Logic: Log mỗi 5 phút (300s)
    if progress.time_spent_seconds - progress.last_logged_time_spent >= 300:
        session_duration = progress.time_spent_seconds - progress.last_logged_time_spent
        
        record_activity(user, {
            'action': 'LEARNING_SESSION',
            'entity_type': 'course',
            'entity_id': str(course.id),
            'course_id': str(course.id),
            'is_critical': False, # Async
            'payload': {
                'block_id': str(block.id),
                'duration': session_duration
            }
        })
        
        progress.last_logged_time_spent = progress.time_spent_seconds
        has_changes = True

    # ---------------------------------------------------------
    # 6. FINAL SAVE (1 Write Query duy nhất)
    # ---------------------------------------------------------
    if has_changes:
        progress.last_accessed = now
        progress.save()

    return UserBlockProgressDomain.from_model(progress, block)


# ==========================================
# SERVICE: MARK QUIZ
# ==========================================

def mark_quiz_as_completed(user_id: str, quiz_id: str, enrollment_id: str, score: float) -> bool:
    """
    Đánh dấu ContentBlock Quiz là hoàn thành.
    Trả về True nếu trạng thái thay đổi từ (Chưa xong -> Xong).
    """
    # 1. Tìm ContentBlock tương ứng với Quiz (Tối ưu query)
    # Dùng .only('id', 'lesson_id') để tiết kiệm RAM
    block = ContentBlock.objects.filter(
        type='quiz', 
        payload__quiz_id=str(quiz_id)
    ).only('id', 'lesson_id').first()

    if not block:
        return False

    # 2. Update hoặc Create UserBlockProgress
    # Sử dụng update_or_create để atomic hơn get_or_create + save
    # Tuy nhiên cần check trạng thái cũ để biết có cần trigger aggregation không
    
    progress, created = UserBlockProgress.objects.get_or_create(
        user_id=user_id,
        block_id=block.id,
        defaults={'enrollment_id': enrollment_id}
    )

    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        
        interaction = progress.interaction_data or {}
        interaction['score'] = score
        progress.interaction_data = interaction

        # Chỉ update các field cần thiết
        progress.save(update_fields=['is_completed', 'completed_at', 'interaction_data'])
        return str(block.lesson_id)

    return None


# ==========================================
# SERVICE: RESET PROGRESS
# ==========================================

def reset_course_progress(user, enrollment_id: str) -> ResetProgressResultDomain:
    """
    Logic: Hard Delete toàn bộ tracking data để user học lại từ đầu.
    """
    try:
        enroll_uuid = uuid.UUID(str(enrollment_id))
    except ValueError:
        raise ValueError("enrollment_id không hợp lệ.")

    # 1. Lấy Enrollment (Check quyền sở hữu của user luôn)
    try:
        enrollment = Enrollment.objects.get(id=enroll_uuid, user=user)
    except Enrollment.DoesNotExist:
        raise PermissionError("Không tìm thấy ghi danh hoặc bạn không có quyền.")

    # 2. Thực hiện Reset (Atomic)
    with transaction.atomic():
        # A. Xóa Tracking chi tiết (Nhóm 1)
        UserBlockProgress.objects.filter(enrollment=enrollment).delete()
        
        # B. Xóa Checkpoint (Nhóm 2)
        # Giả sử bạn đã import model LessonCompletion, ModuleCompletion
        LessonCompletion.objects.filter(enrollment=enrollment).delete()
        ModuleCompletion.objects.filter(enrollment=enrollment).delete()
        
        # C. Xóa/Reset Quiz (Nhóm 3)
        # Tùy policy: Xóa hết hay giữ lại lịch sử điểm? 
        # Ở đây làm theo yêu cầu: Xóa hết để học lại.
        QuizAttempt.objects.filter(enrollment=enrollment).delete()

        # D. Reset Enrollment về 0
        enrollment.percent_completed = 0.0
        enrollment.is_completed = False
        enrollment.completed_at = None
        enrollment.save()

    return ResetProgressResultDomain(
        enrollment_id=enroll_uuid,
        status="success",
        reset_at=timezone.now(),
        message="Đã đặt lại tiến độ học tập thành công."
    )