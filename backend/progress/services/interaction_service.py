import uuid
from django.db import transaction
from django.utils import timezone
from django.db import transaction
from typing import Optional
from django.conf import settings

from content.models import ContentBlock, Lesson, Module
from progress.models import UserBlockProgress
from progress.domains.user_block_progress_domain import UserBlockProgressDomain
from progress.domains.resume_position_domain import ResumePositionDomain
from progress.services.course_progress_service import handle_block_completion



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


def sync_heartbeat(self, user, data: dict) -> UserBlockProgressDomain:
    """
    Xử lý logic Upsert tiến độ chuẩn LMS.
    """
    block_id = data.get('block_id')
    resume_data = data.get('resume_data', {})
    
    # Client gửi request hoàn thành (VD: xem hết video), nhưng Server cần verify
    client_claims_completed = data.get('is_completed', False) 
    time_add = data.get('time_spent_add', 0)

    # --- 1. Validate Input (Sanity Check) ---
    if time_add < 0:
        raise ValueError("Thời gian cộng thêm không thể âm.")
    
    # Chống Spam: Nếu heartbeat set là 10s/lần, mà client gửi cộng 1 tiếng -> Reject hoặc Cap lại
    if time_add > settings.MAX_HEARTBEAT_INTERVAL:
        # Option 1: Cắt xuống max (Soft handle)
        time_add = settings.MAX_HEARTBEAT_INTERVAL 
        # Option 2: Raise Error (Hard handle) - tùy policy
    
    # --- 2. Lấy Content Block (REQUIRED để pass vào Domain Object sau này) ---
    try:
        # Lấy object thật, không chỉ check exists()
        content_block = ContentBlock.objects.get(id=block_id)
    except ContentBlock.DoesNotExist:
        raise ValueError(f"Block {block_id} không tồn tại.")

    # --- 3. Xử lý Persistence ---
    with transaction.atomic():
        # Dùng select_for_update để khóa dòng này, tránh race condition nếu user spam API
        progress, created = UserBlockProgress.objects.select_for_update().get_or_create(
            user=user,
            block_id=block_id,
            defaults={
                'resume_data': resume_data,
                'is_completed': False, # Mặc định tạo mới chưa xong
                'time_spent_seconds': 0
            }
        )

        # --- 4. Logic Server-Side Authority (Học theo Moodle) ---
        
        # A. Cập nhật Resume Data (Vị trí hiện tại)
        progress.resume_data = resume_data
        progress.last_accessed = timezone.now()

        # B. Cộng dồn thời gian an toàn
        if time_add > 0:
            progress.time_spent_seconds += time_add

        # C. Logic tính Completion (Quan trọng nhất)
        # Chỉ update thành True nếu chưa hoàn thành
        if not progress.is_completed:
            should_complete = False

            # Lấy metadata từ JSON Payload
            payload = content_block.payload or {}
            
            # 1. Xử lý Video
            if content_block.type == 'video':
                # Giả sử payload lưu: {"url": "...", "duration": 600}
                duration = payload.get('duration', 0)

                if duration > 0:
                    percent_watched = progress.time_spent_seconds / duration
                    if percent_watched >= settings.COMPLETION_THRESHOLD: # Ngưỡng 95%
                        should_complete = True

            # 2. Xử lý Quiz (Tham chiếu ForeignKey)
            elif content_block.type == 'quiz':
                # Với Quiz, thường logic complete sẽ nằm ở API submit bài thi riêng,
                # không nằm ở heartbeat. Nhưng nếu heartbeat chỉ để track time:
                pass

            # 3. Các loại khác (Text/PDF)
            else:
                # Logic đơn giản: User ở đó đủ lâu (ví dụ 10s) và client báo done
                if client_claims_completed and progress.time_spent_seconds > 5:
                    should_complete = True

            if should_complete:
                progress.is_completed = True
                progress.save()
                # TODO: Trigger Event "Course Progress Update" tại đây
                transaction.on_commit(
                    lambda: handle_block_completion(user, content_block)
                )

        progress.save()

    # --- 5. Return Domain Object ---
    # Bây giờ ta đã có biến 'content_block' để truyền vào hàm này -> FIX LỖI CRASH
    return UserBlockProgressDomain.from_model(progress, content_block)


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


def mark_block_as_complete(self, user, data: dict) -> UserBlockProgressDomain:
    block_id = data.get('block_id') 

    try:
        # Select related để lấy payload xử lý validate
        block = ContentBlock.objects.get(id=block_id)
        # Get progress hiện tại (đã được Heartbeat update time_spent)
        progress = UserBlockProgress.objects.get(user=user, block=block)
    except (ContentBlock.DoesNotExist, UserBlockProgress.DoesNotExist):
        raise ValueError("Không tìm thấy dữ liệu học tập. Vui lòng học thử vài giây trước khi hoàn thành.")

    # 1. Idempotency (Nếu đã xong rồi thì return luôn)
    if progress.is_completed:
        return UserBlockProgressDomain.from_model(progress, block)

    # 2. GỌI HÀM VALIDATE GỘP
    # Nếu không thỏa mãn, hàm này sẽ raise ValueError -> API trả về 400
    validate_completion_policy(block, progress)

    # 3. Update & Ripple Effect (Quan trọng)
    with transaction.atomic():
        progress.is_completed = True
        progress.last_accessed = timezone.now()
        progress.save()
        
        # Kích hoạt tính toán lại tiến độ Lesson/Course
        transaction.on_commit(
            lambda: handle_block_completion(user, block)
        )

    return UserBlockProgressDomain.from_model(progress, block)


##################################################################################################################
##################################################################################################################
##################################################################################################################

# def _find_next_block(self, current_block):
#     """
#     Logic tìm bài tiếp theo cực kỳ phức tạp trong cấu trúc phân cấp.
#     Hierarchy: Course -> Module -> Lesson -> Block
#     """
#     # 1. Tìm block tiếp theo trong cùng Lesson
#     next_in_lesson = ContentBlock.objects.filter(
#         lesson=current_block.lesson,
#         order__gt=current_block.order
#     ).order_by('order').first()
    
#     if next_in_lesson: 
#         return next_in_lesson

#     # 2. Hết Lesson hiện tại -> Tìm Lesson tiếp theo trong cùng Module
#     next_lesson = Lesson.objects.filter(
#         module=current_block.lesson.module,
#         order__gt=current_block.lesson.order
#     ).order_by('order').first()

#     if next_lesson:
#         # Lấy block đầu tiên của lesson mới
#         return next_lesson.content_blocks.order_by('order').first()

#     # 3. Hết Module hiện tại -> Tìm Module tiếp theo trong Course
#     next_module = Module.objects.filter(
#         course=current_block.lesson.module.course,
#         order__gt=current_block.lesson.module.order
#     ).order_by('order').first()

#     if next_module:
#         # Tìm Lesson đầu của Module mới -> Block đầu của Lesson đó
#         first_lesson = next_module.lessons.order_by('order').first()
#         if first_lesson:
#              return first_lesson.content_blocks.order_by('order').first()
    
#     return None # End of Course


# def _build_resume_domain(self, block, user, resume_data, is_completed):
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
    
#     if not last_progress.is_completed:
#         # B1. Chưa xong -> Resume đúng bài cũ
#         target_block = current_block
#         resume_data = last_progress.resume_data
#         is_completed = False
#     else:
#         # B2. Đã xong -> AUTO-ADVANCE -> Tìm bài tiếp theo
#         next_block = _find_next_block(current_block)
        
#         if next_block:
#             # Tìm thấy bài tiếp theo -> Đưa user tới đó (Mới tinh)
#             target_block = next_block
#             resume_data = {} 
#             is_completed = False # Bài mới chưa học
#         else:
#             # Không còn bài nào nữa (Hết khóa học) -> Vẫn ở bài cuối nhưng báo xong
#             target_block = current_block
#             resume_data = last_progress.resume_data
#             is_completed = True

#     # Return Domain (Map từ target_block)
#     # Lưu ý: Cần thêm logic tính % tiến độ khóa học ở đây nếu muốn (xem phần 3)
#     return _build_resume_domain(target_block, user, resume_data, is_completed)