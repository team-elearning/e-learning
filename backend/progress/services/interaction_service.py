import uuid
from django.db import transaction
from django.utils import timezone
from django.db import transaction
from typing import Optional

from content.models import ContentBlock
from progress.models import UserBlockProgress
from progress.models import UserBlockProgress
from progress.domains.user_block_progress_domain import UserBlockProgressDomain
from progress.domains.resume_position_domain import ResumePositionDomain



def sync_heartbeat(user, data: dict) -> UserBlockProgressDomain:
    """
    Xử lý logic Upsert tiến độ.
    Input: User object, data dict (từ Pydantic dump)
    Output: UserBlockProgressDomain (KHÔNG phải Model)
    """
    block_id = data.get('block_id')
    
    # Lấy dữ liệu từ input (Hybrid approach)
    resume_data = data.get('resume_data', {})
    is_completed = data.get('is_completed', False)
    time_add = data.get('time_spent_add', 0)

    # 1. Validate logic nghiệp vụ (nếu cần)
    # Ví dụ: Kiểm tra block có tồn tại không
    if not ContentBlock.objects.filter(id=block_id).exists():
        raise ValueError(f"Block {block_id} không tồn tại.")

    # 2. Thao tác Persistence (ORM)
    # Dùng transaction để đảm bảo tính nhất quán khi cộng dồn thời gian
    with transaction.atomic():
        # Lấy hoặc tạo mới record
        progress, created = UserBlockProgress.objects.get_or_create(
            user=user,
            block_id=block_id,
            defaults={
                'resume_data': resume_data,
                'is_completed': is_completed,
                'time_spent_seconds': time_add
            }
        )

        if not created:
            # Logic update:
            # - resume_data: Ghi đè (Overwrite) để lưu vị trí mới nhất
            # - is_completed: Chỉ update thành True nếu chưa hoàn thành
            # - time_spent_seconds: Cộng dồn (Increment)
            
            progress.resume_data = resume_data
            
            if is_completed and not progress.is_completed:
                progress.is_completed = True
            
            if time_add > 0:
                progress.time_spent_seconds += time_add
            
            progress.save()

    # 3. Convert Model -> Domain và Return
    return UserBlockProgressDomain.from_model(progress)


def get_interaction_status(user, block_id: str) -> UserBlockProgressDomain:
    """
    Lấy trạng thái học tập.
    Luôn trả về một Domain Object (kể cả khi chưa học).
    """
    try:
        # Validate UUID format
        uuid_obj = uuid.UUID(str(block_id))
    except ValueError:
        raise ValueError("block_id không hợp lệ.")

    try:
        # 1. Thử lấy từ DB
        progress = UserBlockProgress.objects.get(user=user, block_id=uuid_obj)
        
        # 2. Found -> Convert sang Domain
        return UserBlockProgressDomain.from_model(progress)

    except UserBlockProgress.DoesNotExist:
        # 3. Not Found -> Trả về một Domain Object RỖNG (Transient/Non-persisted)
        # Điều này giúp Frontend không bị lỗi null, và logic thống nhất.
        return UserBlockProgressDomain(
            id=None, # Chưa có ID vì chưa lưu DB
            user_id=user.id,
            block_id=uuid_obj,
            is_completed=False,
            time_spent_seconds=0,
            resume_data={},
            last_accessed=None,
            score=None
        )
    

def mark_block_as_complete(user, data: dict) -> UserBlockProgressDomain:
    """
    Xử lý logic đánh dấu hoàn thành Block.
    Validate chặt chẽ dựa trên dữ liệu heartbeat đã tích lũy.
    Output: UserBlockProgressDomain
    """
    block_id = data.get('block_id') 
    
    # 1. Lấy Block và Progress hiện tại
    # Chúng ta dùng get_or_create để đảm bảo record tồn tại, 
    # nhưng logic validate sẽ chặn nếu time_spent = 0
    try:
        block = ContentBlock.objects.get(id=block_id)
        progress, created = UserBlockProgress.objects.get_or_create(
            user=user, block=block
        )
    except ContentBlock.DoesNotExist:
        raise ValueError(f"Block {block_id} không tồn tại.")

    # 2. Idempotency Check (Quan trọng)
    # Nếu đã hoàn thành rồi -> Trả về Domain luôn, không xử lý lại.
    if progress.is_completed:
        return UserBlockProgressDomain.from_model(progress)

    # 3. VALIDATION LOGIC (Kiểm tra điều kiện "Đủ")
    # Logic này ngăn chặn việc user gọi API complete mà chưa học
    if block.type == 'VIDEO':
        validate_video_completion(block, progress)
    
    elif block.type in ['TEXT', 'PDF', 'DOCUMENT']:
        validate_reading_completion(block, progress)
        
    # elif block.block_type == 'QUIZ':
    #     self._validate_quiz_completion(block, progress)

    # 4. Update & Persistence
    # Dùng transaction atomic nếu sau này bạn có trigger update Course/Module progress
    with transaction.atomic():
        progress.is_completed = True
        progress.last_accessed = timezone.now()
        progress.save()
        
        # TODO: Trigger event/signal để update Module Progress nếu cần
        # self._check_and_update_module_completion(user, block.module_id)

    # 5. Convert Model -> Domain và Return
    return UserBlockProgressDomain.from_model(progress)


def validate_video_completion(self, block, progress):
    """
    Logic: Video phải xem > 90% thời lượng (hoặc config dynamic).
    Dữ liệu time_spent_seconds được tích lũy từ Heartbeat API.
    """
    video_duration = block.duration_seconds # Trường duration của ContentBlock
    
    # Fail-safe: Nếu video không có duration (ví dụ livestream hoặc lỗi data),
    # ta có thể cho qua hoặc yêu cầu tối thiểu 30s.
    if not video_duration:
        return 

    required_time = video_duration * 0.9
    
    # Lấy time đã học (từ DB - do heartbeat cập nhật)
    current_time_spent = progress.time_spent_seconds
    
    # Validation
    if current_time_spent < required_time:
        # Logic phụ: Check thêm timestamp hiện tại (resume_data) để chặt chẽ hơn
        # (Tránh trường hợp user tua đến cuối nhưng tổng thời gian xem chưa đủ)
        current_timestamp = progress.resume_data.get('video_timestamp', 0)
        
        # Chi tiết lỗi trả về giúp FE hiển thị thông báo rõ ràng
        missing_seconds = int(required_time - current_time_spent)
        raise ValueError(
            f"Bạn chưa xem đủ thời lượng yêu cầu. Hãy xem thêm {missing_seconds} giây nữa."
        )


def validate_reading_completion(self, block, progress):
    """
    Logic: Text/PDF phải đợi X giây (tránh click xong out ngay).
    """
    min_read_time = getattr(block, 'min_seconds_required', 5) # Default 5s nếu field null
    
    if not min_read_time:
        min_read_time = 5

    if progress.time_spent_seconds < min_read_time:
        raise ValueError(
            f"Vui lòng đọc nội dung ít nhất {min_read_time} giây trước khi hoàn thành."
        )
    

def get_course_resume_position(self, user, course_id: str) -> Optional[ResumePositionDomain]:
    """
    Logic tìm điểm 'Resume'.
    Input: user, course_id
    Output: ResumePositionDomain hoặc None (nếu course rỗng)
    """
    # 1. Validate input
    try:
        course_uuid = uuid.UUID(str(course_id))
    except ValueError:
        raise ValueError("Course ID không hợp lệ.")

    # 2. Tìm lịch sử học tập gần nhất (Last Access)
    # Query: Tìm record UserBlockProgress thuộc course này, có last_accessed mới nhất
    last_progress = UserBlockProgress.objects.filter(
        user=user,
        block__lesson__module__course_id=course_uuid
    ).select_related(
        'block__lesson__module' # Join để lấy ID lesson/module tránh N+1
    ).order_by('-last_accessed').first()

    # CASE A: User đã học -> Trả về vị trí cũ
    if last_progress:
        return ResumePositionDomain.from_model(last_progress)

    # CASE B: User chưa học (New User) -> Tìm bài đầu tiên của khóa học
    # Logic: Course -> Module (order min) -> Lesson (order min) -> Block (order min)
    first_block = ContentBlock.objects.filter(
        lesson__module__course_id=course_uuid
    ).order_by(
        'lesson__module__order',
        'lesson__order',
        'order'
    ).first()

    if first_block:
        return ResumePositionDomain.from_first_block(first_block)

    # CASE C: Course chưa có bài nào
    return None