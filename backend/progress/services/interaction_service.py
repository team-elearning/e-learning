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
            
            # Rule 1: Dựa vào thời lượng (Nếu là Video/Audio)
            if content_block.duration_seconds and content_block.duration_seconds > 0:
                percent_watched = progress.time_spent_seconds / content_block.duration_seconds
                if percent_watched >= settings.COMPLETION_THRESHOLD:
                    should_complete = True
            
            # Rule 2: Nếu không có thời lượng (VD: PDF), tin client NHƯNG phải có time_spent tối thiểu
            # (Ví dụ: Phải mở PDF ít nhất 10 giây)
            elif client_claims_completed and progress.time_spent_seconds > 10:
                should_complete = True

            if should_complete:
                progress.is_completed = True
                # TODO: Trigger Event "Course Progress Update" tại đây
                # self.course_service.update_course_progress(user, content_block.course_id)

        progress.save()

    # --- 5. Return Domain Object ---
    # Bây giờ ta đã có biến 'content_block' để truyền vào hàm này -> FIX LỖI CRASH
    return UserBlockProgressDomain.from_model(progress, content_block)


# def mark_block_as_complete(user, data: dict) -> UserBlockProgressDomain:
#     """
#     Xử lý logic đánh dấu hoàn thành Block.
#     Validate chặt chẽ dựa trên dữ liệu heartbeat đã tích lũy.
#     Output: UserBlockProgressDomain
#     """
#     block_id = data.get('block_id') 

#     # 1. Lấy Block và Progress hiện tại
#     # Chúng ta dùng get_or_create để đảm bảo record tồn tại, 
#     # nhưng logic validate sẽ chặn nếu time_spent = 0
#     try:
#         block = ContentBlock.objects.get(id=block_id)
#         progress, created = UserBlockProgress.objects.get_or_create(
#             user=user, block=block
#         )
#     except ContentBlock.DoesNotExist:
#         raise ValueError(f"Block {block_id} không tồn tại hoặc chưa được cập nhật.")

#     # 2. Idempotency Check (Quan trọng)
#     # Nếu đã hoàn thành rồi -> Trả về Domain luôn, không xử lý lại.
#     if progress.is_completed:
#         return UserBlockProgressDomain.from_model(progress)

#     # 3. VALIDATION LOGIC (Kiểm tra điều kiện "Đủ")
#     # Logic này ngăn chặn việc user gọi API complete mà chưa học
#     if block.type == 'VIDEO':
#         validate_completion_dynamic(block, progress)
    
#     elif block.type in ['TEXT', 'PDF', 'DOCUMENT']:
#         validate_completion_dynamic(block, progress)
        
#     # elif block.block_type == 'QUIZ':
#     #     self._validate_quiz_completion(block, progress)

#     # 4. Update & Persistence
#     # Dùng transaction atomic nếu sau này bạn có trigger update Course/Module progress
#     with transaction.atomic():
#         progress.is_completed = True
#         progress.last_accessed = timezone.now()
#         progress.save()
        
#         # TODO: Trigger event/signal để update Module Progress nếu cần
#         # self._check_and_update_module_completion(user, block.module_id)

#     # 5. Convert Model -> Domain và Return
#     return UserBlockProgressDomain.from_model(progress)


# def validate_completion_dynamic(self, block, progress):
#     """
#     Logic: Video phải xem > 90% thời lượng (hoặc config dynamic).
#     Dữ liệu time_spent_seconds được tích lũy từ Heartbeat API.
#     """
#     video_duration = block.duration_seconds # Trường duration của ContentBlock
    
#     # Fail-safe: Nếu video không có duration (ví dụ livestream hoặc lỗi data),
#     # ta có thể cho qua hoặc yêu cầu tối thiểu 30s.
#     if not video_duration:
#         return 

#     required_time = video_duration * 0.9
    
#     # Lấy time đã học (từ DB - do heartbeat cập nhật)
#     current_time_spent = progress.time_spent_seconds
    
#     # Validation
#     if current_time_spent < required_time:
#         # Logic phụ: Check thêm timestamp hiện tại (resume_data) để chặt chẽ hơn
#         # (Tránh trường hợp user tua đến cuối nhưng tổng thời gian xem chưa đủ)
#         current_timestamp = progress.resume_data.get('video_timestamp', 0)
        
#         # Chi tiết lỗi trả về giúp FE hiển thị thông báo rõ ràng
#         missing_seconds = int(required_time - current_time_spent)
#         raise ValueError(
#             f"Bạn chưa xem đủ thời lượng yêu cầu. Hãy xem thêm {missing_seconds} giây nữa."
#         )


# def validate_completion_dynamic(self, block, progress):
#     criteria = block.completion_criteria # Lấy rule từ DB
    
#     # 1. Rule chung cho Video
#     if block.type == 'VIDEO':
#         required_percent = criteria.get('min_percent', 90) # Default 90% nếu không config
        
#         if not block.duration_seconds: return # Skip check nếu lỗi data
        
#         required_time = block.duration_seconds * (required_percent / 100)
#         if progress.time_spent_seconds < required_time:
#              raise ValueError(f"Yêu cầu xem tối thiểu {required_percent}% thời lượng.")

#     # 2. Rule chung cho Reading
#     elif block.type in ['PDF', 'TEXT']:
#         required_seconds = criteria.get('min_seconds', 5) # Default 5s
        
#         if progress.time_spent_seconds < required_seconds:
#             raise ValueError(f"Cần đọc tối thiểu {required_seconds} giây.")

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