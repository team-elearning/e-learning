import uuid
from django.db import transaction

from core.exceptions import DomainValidationError
from progress.models import UserBlockProgress, ContentBlock
from progress.domains.user_block_progress_domain import UserBlockProgressDomain



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