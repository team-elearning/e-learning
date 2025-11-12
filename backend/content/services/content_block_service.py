import uuid
from typing import List, Dict, Any
from django.db import transaction, models
from django.db.models import F

from custom_account.models import UserModel
from content.models import ContentBlock, LessonVersion, Enrollment
from content.domains.content_block_domain import ContentBlockDomain 
from content.services.exceptions import LessonVersionNotFoundError, ContentBlockNotFoundError, DomainError, BlockMismatchError, NotEnrolledError, VersionNotPublishedError



# --- Helper Function ---

def _get_lesson_version_model(lesson_version_id: uuid.UUID) -> LessonVersion:
    """
    Helper riêng tư để lấy LessonVersion model.
    """
    try:
        return LessonVersion.objects.get(id=lesson_version_id)
    except LessonVersion.DoesNotExist:
        raise LessonVersionNotFoundError("LessonVersion not found.")

def _get_block_model(block_id: uuid.UUID) -> ContentBlock:
    """
    Helper riêng tư để lấy ContentBlock model.
    """
    try:
        return ContentBlock.objects.get(id=block_id)
    except ContentBlock.DoesNotExist:
        raise ContentBlockNotFoundError("ContentBlock not found.")


# --- Service Functions ---

def list_blocks_for_version(lesson_version_id: uuid.UUID) -> List[ContentBlockDomain]:
    """
    Lấy danh sách các content block cho một lesson version,
    trả về list các domain object.
    (Tương tự list_all_users_for_admin)
    """
    version_model = _get_lesson_version_model(lesson_version_id)
    
    # Model đã có Meta ordering = ['position'], nên .all() đã được sắp xếp
    block_models = version_model.content_blocks.all()
    
    # Chuyển đổi Model -> Domain
    block_domains = [ContentBlockDomain.from_model(block) for block in block_models]
    return block_domains


@transaction.atomic
def create_block(lesson_version_id: uuid.UUID, data: Dict[str, Any]) -> ContentBlockDomain:
    """
    Tạo một content block mới.
    """
    version_model = _get_lesson_version_model(lesson_version_id)
    
    # --- Business Logic: Gán position ---
    # Block mới luôn được thêm vào cuối cùng
    current_max = version_model.content_blocks.aggregate(
        max_pos=models.Max('position')
    )['max_pos']
    
    next_position = 0 if current_max is None else current_max + 1
    
    # Tạo Domain object trước (giống register_user)
    block_domain = ContentBlockDomain(
        type=data['type'],
        payload=data.get('payload', {}),
        position=next_position
    )
    
    # (Nếu domain có validation)
    # block_domain.validate() 
    
    # Chuyển Domain -> Model
    block_model = block_domain.to_model()
    block_model.lesson_version = version_model # Gán Foreign Key
    block_model.save()
    
    # Trả về domain object mới nhất từ model đã lưu
    return ContentBlockDomain.from_model(block_model)


def get_block_by_id(block_id: uuid.UUID) -> ContentBlockDomain:
    """
    Lấy một block theo ID.
    (Tương tự get_user_by_id)
    """
    block_model = _get_block_model(block_id)
    return ContentBlockDomain.from_model(block_model)


@transaction.atomic
def update_block(block_id: uuid.UUID, updates: Dict[str, Any]) -> ContentBlockDomain:
    """
    Cập nhật một content block.
    (Tương tự update_user)
    """
    block_model = _get_block_model(block_id)
    
    # --- Business Logic: Ngăn chặn thay đổi nhạy cảm ---
    if 'position' in updates:
        raise DomainError("Cannot change 'position' directly. Use the /reorder/ endpoint.")
    if 'lesson_version' in updates or 'lesson_version_id' in updates:
        raise DomainError("Cannot move a block to a different lesson version.")
    
    # Chuyển Model -> Domain
    domain = ContentBlockDomain.from_model(block_model)
    
    # Áp dụng updates và validate (nếu có)
    # Giả định domain object có phương thức này
    domain.apply_updates(updates) 
    
    # Lưu thay đổi vào database (giống hệt update_user)
    for key, value in updates.items():
        if hasattr(block_model, key):
            setattr(block_model, key, value)
            
    block_model.save()
    
    return domain # Trả về domain đã cập nhật


@transaction.atomic
def delete_block(block_id: uuid.UUID) -> None:
    """
    Xóa một content block và cập nhật lại position của các block sau nó.
    (Tương tự delete_user, nhưng có thêm logic)
    """
    block_model = _get_block_model(block_id)
    
    lesson_version = block_model.lesson_version
    deleted_position = block_model.position

    # 1. Xóa block
    block_model.delete()
    
    # 2. Business Logic: Cập nhật lại position
    # Dồn các block ở vị trí sau lên 1 bậc (position - 1)
    ContentBlock.objects.filter(
        lesson_version=lesson_version,
        position__gt=deleted_position
    ).update(position=F('position') - 1)


@transaction.atomic
def reorder_blocks(lesson_version_id: uuid.UUID, ordered_ids: List[str]) -> None:
    """
    Sắp xếp lại vị trí của tất cả các block trong một version.
    (Tương tự synchronize_roles ở khía cạnh bulk update)
    """
    version_model = _get_lesson_version_model(lesson_version_id)
    
    # Lấy tất cả block hiện tại
    blocks = ContentBlock.objects.filter(lesson_version=version_model)
    block_map = {str(block.id): block for block in blocks}
    
    # --- Business Logic: Validate input ---
    current_ids = set(block_map.keys())
    new_ids = set(ordered_ids)
    
    if current_ids != new_ids:
        raise BlockMismatchError(
            "The list of IDs provided does not match the blocks for this version."
        )

    # Cập nhật position mới
    update_list = []
    for i, block_id_str in enumerate(ordered_ids):
        block = block_map.get(block_id_str)
        
        # Chỉ update nếu position thực sự thay đổi
        if block and block.position != i:
            block.position = i
            update_list.append(block)
    
    # Dùng bulk_update để tối ưu performance (1 query)
    if update_list:
        ContentBlock.objects.bulk_update(update_list, ['position'])


def get_public_blocks_for_version(
    user: UserModel, 
    lesson_version_id: uuid.UUID
) -> List[ContentBlockDomain]:
    """
    Service nghiệp vụ cho HỌC SINH (public).
    Kiểm tra quyền ghi danh và trạng thái published.
    (Giống hệt pattern của lesson_service.get_published_lesson_content)
    """
    try:
        # Lấy LessonVersion và join sẵn
        version = LessonVersion.objects.select_related(
            'lesson__module__course'
        ).get(pk=lesson_version_id)
        
    except LessonVersion.DoesNotExist:
        raise LessonVersionNotFoundError("Không tìm thấy phiên bản bài học.")

    if version.status != 'published':
        raise VersionNotPublishedError("Nội dung bài học chưa được xuất bản.")

    # Kiểm tra nghiệp vụ 2: Đã ghi danh chưa?
    # (Bỏ qua nếu là admin)
    if not user.is_staff:
        course = version.lesson.module.course
        is_enrolled = Enrollment.objects.filter(
            user=user, 
            course=course
        ).exists()
        
        if not is_enrolled:
            raise NotEnrolledError("Bạn phải ghi danh vào khóa học để xem nội dung này.")
            
    # Nếu mọi thứ OK, lấy danh sách blocks (đã được sắp xếp)
    block_models = version.content_blocks.all()
    
    # Chuyển Model -> Domain
    block_domains = [ContentBlockDomain.from_model(block) for block in block_models]
    return block_domains