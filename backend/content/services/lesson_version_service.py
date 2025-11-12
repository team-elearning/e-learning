import logging
from typing import Optional, Any, Dict, List
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Max

from content.models import Lesson, LessonVersion, ContentBlock
from custom_account.models import UserModel 
from content.domains.lesson_version_domain import LessonVersionDomain
from content.services import exceptions as lesson_exceptions 



logger = logging.getLogger(__name__)

def list_versions_for_lesson(lesson_id: str) -> List[LessonVersionDomain]:
    """
    Lấy danh sách các phiên bản cho một bài học.
    
    LƯU Ý: Không prefetch 'content_blocks' ở đây
    để tránh tải quá nhiều dữ liệu trong một view list.
    Domain 'from_model' sẽ chỉ nạp "vỏ" (shell).
    """
    version_models = LessonVersion.objects.filter(
        lesson_id=lesson_id
    ).select_related('author').order_by('-version')
    
    # from_model sẽ tạo domain mà không có 'content_blocks'
    version_domains = [LessonVersionDomain.from_model(v) for v in version_models]
    return version_domains


@transaction.atomic
def create_lesson_version(lesson_id: str, author: UserModel, data: Dict[str, Any]) -> LessonVersionDomain:
    """
    Tạo một "Cụm" LessonVersion mới (bao gồm cả ContentBlocks).
    
    Hàm này sẽ:
    1. Tạo model LessonVersion (cái "vỏ").
    2. Duyệt qua 'content_blocks' trong 'data' và tạo các model ContentBlock.
    3. Cập nhật trường JSON 'content' (cache) trên LessonVersion.
    4. Trả về LessonVersionDomain đã được hydrate đầy đủ.
    """
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
    except Lesson.DoesNotExist:
        logger.warning(f"Thất bại khi tạo version: Lesson {lesson_id} không tìm thấy.")
        raise lesson_exceptions.LessonNotFoundError("Bài học không tìm thấy.")

    # Business Rule: Chỉ cho phép một bản 'draft' tại một thời điểm
    if LessonVersion.objects.filter(lesson=lesson, status='draft').exists():
        raise lesson_exceptions.DomainError(
            "Bài học này đã có một phiên bản nháp. Vui lòng chỉnh sửa phiên bản đó."
        )

    # Lấy số version mới nhất và + 1
    last_version_data = LessonVersion.objects.filter(lesson=lesson).aggregate(max_version=Max('version'))
    next_version_num = (last_version_data['max_version'] or 0) + 1

    # Tạo "vỏ" LessonVersion ---
    lv_domain_shell = LessonVersionDomain(
        lesson_id=lesson.id,
        author_id=author.id,
        version=next_version_num,
        status='draft',
        change_summary=data.get('change_summary')
    )
    
    lv_model = LessonVersion(
        id=lv_domain_shell.id,
        lesson=lesson,
        author=author,
        version=lv_domain_shell.version,
        status=lv_domain_shell.status,
        change_summary=lv_domain_shell.change_summary
    )
    lv_model.save()
    
    # --- 2. Tạo các ContentBlock con ---
    blocks_data = data.get('content_blocks', [])
    blocks_to_create = []
    
    for cb_data in blocks_data:
        # (Ở đây có thể validate cb_data bằng Pydantic DTO nếu cần)
        blocks_to_create.append(
            ContentBlock(
                lesson_version=lv_model,
                type=cb_data.get('type'),
                position=cb_data.get('position', 0),
                payload=cb_data.get('payload', {})
            )
        )

    if blocks_to_create:
        ContentBlock.objects.bulk_create(blocks_to_create)

    # --- 3. Lấy lại Domain đầy đủ và Cập nhật cache ---
    # Cách sạch nhất để có domain đầy đủ là gọi 'get' (đã có prefetch)
    try:
        full_domain = get_lesson_version_by_id(lv_model.id)
        
        # Cập nhật trường JSON 'content' (cache)
        lv_model.content = full_domain.content # Dùng @property
        lv_model.save(update_fields=['content'])
        
        return full_domain
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng khi hydrate/cache version {lv_model.id}: {e}", exc_info=True)
        # Ném ra lỗi để transaction rollback
        raise lesson_exceptions.DomainError(f"Lỗi khi lưu cache nội dung: {e}")


def get_lesson_version_by_id(version_id: str) -> LessonVersionDomain:
    """
    Lấy một "Cụm" LessonVersion đầy đủ bằng ID,
    bao gồm tất cả ContentBlock của nó.
    """
    try:
        version_model = LessonVersion.objects.select_related(
            'lesson', 'author'
        ).prefetch_related(
            'content_blocks' 
        ).get(pk=version_id)
        
        # from_model của bạn sẽ tự động đọc 'content_blocks'
        # (hoặc 'content_blocks_prefetched' nếu bạn đặt tên prefetch)
        return LessonVersionDomain.from_model(version_model)
        
    except LessonVersion.DoesNotExist:
        raise lesson_exceptions.VersionNotFoundError("Phiên bản bài học không tìm thấy.")


@transaction.atomic
def update_lesson_version(version_id: str, updates: Dict[str, Any]) -> LessonVersionDomain:
    """
    Cập nhật một "Cụm" LessonVersion.
    
    Hàm này sẽ:
    1. Cập nhật các trường đơn giản (vd: change_summary).
    2. Đồng bộ (Sync) 'content_blocks':
        - Xóa các block không có trong 'updates'.
        - Cập nhật các block đã có.
        - Tạo các block mới.
    3. Cập nhật cache JSON 'content'.
    """
    try:
        version_model = LessonVersion.objects.get(pk=version_id)
    except LessonVersion.DoesNotExist:
        raise lesson_exceptions.VersionNotFoundError("Phiên bản bài học không tìm thấy.")

    # Business Rule: Không cho phép sửa phiên bản đã 'published'
    if version_model.status == 'published':
        raise lesson_exceptions.DomainError("Không thể chỉnh sửa phiên bản đã được xuất bản.")
        
    update_fields = [] # Cho model LessonVersion

    # --- 1. Cập nhật trường đơn giản ---
    if 'change_summary' in updates:
        version_model.change_summary = updates['change_summary']
        update_fields.append('change_summary')
    
    # (Bạn có thể thêm các trường khác như 'title', v.v... ở đây)

    # --- Đồng bộ "Cụm" ContentBlock ---
    if 'content_blocks' in updates:
        new_blocks_data = updates['content_blocks']
        
        # Lấy ID các block hiện tại và các block mới
        current_block_models = {str(b.id): b for b in version_model.content_blocks.all()}
        current_block_ids = set(current_block_models.keys())
        new_block_ids = set()

        blocks_to_create = []
        blocks_to_update = []
        
        for cb_data in new_blocks_data:
            cb_id = cb_data.get('id')
            
            if cb_id and cb_id in current_block_ids:
                # === UPDATE (Cập nhật) ===
                block_model = current_block_models[cb_id]
                block_model.type = cb_data.get('type')
                block_model.position = cb_data.get('position', 0)
                block_model.payload = cb_data.get('payload', {})
                blocks_to_update.append(block_model)
                new_block_ids.add(cb_id)
            
            else:
                # === CREATE (Tạo mới) ===
                blocks_to_create.append(
                    ContentBlock(
                        lesson_version=version_model,
                        type=cb_data.get('type'),
                        position=cb_data.get('position', 0),
                        payload=cb_data.get('payload', {})
                    )
                )
        
        # === DELETE (Xóa) ===
        ids_to_delete = current_block_ids - new_block_ids
        if ids_to_delete:
            ContentBlock.objects.filter(id__in=ids_to_delete).delete()
            
        # Thực thi Cập nhật và Tạo mới
        if blocks_to_update:
            ContentBlock.objects.bulk_update(blocks_to_update, ['type', 'position', 'payload'])
        
        if blocks_to_create:
            ContentBlock.objects.bulk_create(blocks_to_create)

    # --- 3. Lưu, Lấy lại và Cập nhật Cache ---
    if update_fields:
        version_model.save(update_fields=update_fields)
        
    # Lấy lại domain mới nhất từ DB
    updated_domain = get_lesson_version_by_id(version_id)
    
    # Cập nhật cache JSON
    version_model.content = updated_domain.content # Dùng @property
    version_model.save(update_fields=['content'])
    
    return updated_domain


def delete_lesson_version(version_id: str) -> bool:
    """
    Xóa một phiên bản LessonVersion.
    'on_delete=models.CASCADE' sẽ tự động xóa các ContentBlock con.
    
    Business Rules:
    1. Không cho phép xóa phiên bản đã 'published'.
    2. Không cho phép xóa phiên bản duy nhất (v1) của bài học.
    """
    try:
        version_model = LessonVersion.objects.get(pk=version_id)
    except LessonVersion.DoesNotExist:
        raise lesson_exceptions.VersionNotFoundError("Phiên bản bài học không tìm thấy.")

    if version_model.status == 'published':
        raise lesson_exceptions.DomainError("Không thể xóa phiên bản đã được xuất bản.")

    version_count = LessonVersion.objects.filter(lesson=version_model.lesson).count()
    if version_count <= 1:
        raise lesson_exceptions.DomainError("Không thể xóa phiên bản duy nhất của bài học.")

    version_model.delete()
    return True


@transaction.atomic
def set_version_status(version_id: str, new_status: str) -> LessonVersionDomain:
    """
    Cập nhật trạng thái ('status') của một phiên bản.
    (Hàm này không thay đổi, vì nó không tác động đến ContentBlock)
    """
    try:
        version_model = LessonVersion.objects.get(pk=version_id)
    except LessonVersion.DoesNotExist:
        raise lesson_exceptions.VersionNotFoundError("Phiên bản bài học không tìm thấy.")
        
    current_status = version_model.status
    
    if new_status == current_status:
        return get_lesson_version_by_id(version_id) # Trả về domain đầy đủ

    # Validate luồng chuyển trạng thái
    # (Lấy lại VALID_STATUSES từ domain)
    valid_transitions = {
        'draft': ['review', 'published'],
        'review': ['draft', 'published'],
        'published': ['draft', 'archived'], # Giả sử có thêm 'archived'
        'archived': ['draft']
    }
    
    allowed_next_statuses = valid_transitions.get(current_status, [])
    if new_status not in allowed_next_statuses:
        raise lesson_exceptions.DomainError(
            f"Không thể chuyển trạng thái từ '{current_status}' sang '{new_status}'."
        )

    # Xử lý khi publish bản mới
    if new_status == 'published':
        LessonVersion.objects.filter(
            lesson=version_model.lesson, 
            status='published'
        ).exclude(
            pk=version_id
        ).update(status='draft') # Hoặc 'archived' tùy logic của bạn
    
    # Cập nhật trạng thái
    version_model.status = new_status
    version_model.save(update_fields=['status'])
    
    # Trả về domain đầy đủ (đã có prefetch)
    return get_lesson_version_by_id(version_id)