import re
import uuid
from django.db import transaction
from django.db.models import F, Max
from typing import List, Dict, Any, Tuple

from custom_account.models import UserModel
from content.models import ContentBlock, Enrollment, Lesson
from content.domains.content_block_domain import ContentBlockDomain 
from quiz.services.quiz_course_service import create_quiz, patch_quiz
from core.exceptions import LessonVersionNotFoundError, ContentBlockNotFoundError, DomainError, BlockMismatchError, NotEnrolledError, VersionNotPublishedError
from quiz.models import Quiz
from media.services.file_service import commit_files_by_ids_for_object



# # --- Helper Function ---

# def _get_lesson_model(lesson_id: uuid.UUID) -> Lesson:
#     """
#     Helper riêng tư để lấy LessonVersion model.
#     """
#     try:
#         return Lesson.objects.get(id=lesson_id)
#     except Lesson.DoesNotExist:
#         raise LessonVersionNotFoundError("LessonVersion not found.")

# def _get_block_model(block_id: uuid.UUID) -> ContentBlock:
#     """
#     Helper riêng tư để lấy ContentBlock model.
#     """
#     try:
#         return ContentBlock.objects.get(id=block_id)
#     except ContentBlock.DoesNotExist:
#         raise ContentBlockNotFoundError("ContentBlock not found.")


# # --- Service Functions ---

# def list_blocks_for_version(lesson_id: uuid.UUID) -> List[ContentBlockDomain]:
#     """
#     Lấy danh sách các content block cho một lesson version,
#     trả về list các domain object.
#     (Tương tự list_all_users_for_admin)
#     """
#     version_model = _get_lesson_model(lesson_id)
    
#     # Model đã có Meta ordering = ['position'], nên .all() đã được sắp xếp
#     block_models = version_model.content_blocks.all()
    
#     # Chuyển đổi Model -> Domain
#     block_domains = [ContentBlockDomain.from_model(block) for block in block_models]
#     return block_domains


# ==========================================
# PUBLIC INTERFACE (GET)
# ==========================================

def get_content_blocks(lesson_id: uuid.UUID) -> list[ContentBlockDomain]:
    """
    Lấy danh sách content blocks của một lesson.
    Sắp xếp theo position tăng dần.
    """
    # 1. Validate Lesson tồn tại
    # (Có thể dùng filter().exists() để nhẹ hơn get(), nhưng get() an toàn hơn về logic)
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        raise Lesson.DoesNotExist(f"Bài học với ID '{lesson_id}' không tồn tại.")
    
    # 2. Query tối ưu
    # Dùng select_related 'quiz_ref' để lấy luôn thông tin Quiz nếu có
    # Dùng filter(lesson_id=...) để đỡ phải join bảng Lesson lần nữa
    blocks = ContentBlock.objects.select_related('quiz_ref')\
        .filter(lesson_id=lesson_id)\
        .order_by('position')

    # 3. Map sang Domain
    return [ContentBlockDomain.from_model_summary(block) for block in blocks]


def get_content_block_detail(block_id: uuid.UUID) -> ContentBlockDomain:
        """
        Lấy chi tiết 1 block (Dạng Detail - Nặng).
        Dùng khi bấm vào nút 'Edit' của 1 block.
        """
        try:
            # Cần lấy cả quiz_ref để fill dữ liệu nếu là quiz block
            block = ContentBlock.objects.select_related('quiz_ref').get(id=block_id)
            
            # Map sang Detail Domain
            return ContentBlockDomain.from_model_detail(block)
            
        except ContentBlock.DoesNotExist:
            raise DomainError(f"Content Block với ID '{block_id}' không tồn tại.")


# ==========================================
# PUBLIC INTERFACE (CREATE)
# ==========================================

HTML_UUID_PATTERN = re.compile(
    r'data-file-id=["\']([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})["\']'
)


def _extract_file_ids_from_html(html_content: str) -> List[str]:
    """
    Tìm tất cả UUID nằm trong thuộc tính data-file-id="UUID" của chuỗi HTML.
    Regex này tìm chuỗi: data-file-id="[36 ký tự UUID]"
    """
    if not html_content:
        return []
    
    # Pattern tìm UUID chuẩn (8-4-4-4-12)
    return HTML_UUID_PATTERN.findall(html_content)


@transaction.atomic
def create_content_block(
    lesson_id: uuid.UUID, 
    data: dict, 
    actor: UserModel
) -> ContentBlockDomain:
    """
    Tạo block rỗng (Skeleton).
    FE thường chỉ gửi: {"type": "rich_text", "position": ...} hoặc thậm chí không gửi gì.
    """
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        raise Lesson.DoesNotExist(f"Bài học {lesson_id} không tồn tại.")

    # 1. Tính Position (Giữ nguyên logic của bạn - rất chuẩn)
    # Nếu FE gửi position cụ thể (ví dụ chèn vào giữa), ưu tiên dùng nó
    # Còn không thì append xuống cuối.
    req_position = data.get('position')
    if req_position is not None:
         # TODO: Nếu chèn giữa, cần logic đẩy các block phía sau dồn xuống (+1 position)
         # Để đơn giản giai đoạn 1: Cứ append xuống cuối như logic cũ của bạn
         pass 

    max_pos = ContentBlock.objects.filter(lesson=lesson).aggregate(Max('position'))['position__max']
    position = 0 if max_pos is None else max_pos + 1

    # 2. Xử lý Type & Payload mặc định
    block_type = data.get('type', 'rich_text') # Mặc định là text
    
    # Payload rỗng ban đầu
    initial_payload = {}
    quiz_ref_model = None

    if block_type == 'rich_text':
        initial_payload = {'html_content': ''}

    elif block_type == 'quiz':
        # Với Quiz, có thể tạo sẵn 1 cái Quiz draft rỗng luôn
        new_quiz_domain = create_quiz(data={"title": "Untitled Quiz"}, actor=actor)

        try:
            quiz_ref_model = Quiz.objects.get(id=new_quiz_domain.id)
        except Quiz.DoesNotExist:
            raise ValueError("Lỗi hệ thống: Không tìm thấy Quiz vừa tạo.")

        initial_payload = {'quiz_id': str(new_quiz_domain.id)}

    elif block_type in ['video', 'pdf', 'docx', 'file', 'audio']:
        # Media thì để rỗng. 
        # Frontend check: if (!payload.video_id) => Hiện nút "Upload Video"
        initial_payload = {}

    # 3. Tạo ngay lập tức
    new_block = ContentBlock.objects.create(
        lesson=lesson,
        type=block_type,
        payload=initial_payload,
        position=position,
        quiz_ref=quiz_ref_model
    )
    
    return ContentBlockDomain.from_model_detail(new_block)


@transaction.atomic
def create_content_block_template(
    lesson_id: uuid.UUID, 
    data: dict, 
    actor: UserModel
) -> ContentBlockDomain:
    """
    Tạo ContentBlock mới cho bài học.
    Hỗ trợ xử lý tự động cho: Quiz (tạo mới), RichText (quét file), Media (gắn file).
    """
    # 1. Tìm Lesson cha (Validate tồn tại)
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        raise Lesson.DoesNotExist(f"Bài học với ID '{lesson_id}' không tồn tại.")

    # 2. Tính toán Position (Logic chuẩn giống create_lesson)
    # Lấy vị trí lớn nhất hiện tại trong lesson này
    max_position = ContentBlock.objects.filter(lesson=lesson).aggregate(Max('position'))['position__max']
    
    # Nếu chưa có block nào (None) -> -1. Kết quả bắt đầu từ 0.
    current_max = max_position if max_position is not None else -1
    position = current_max + 1

    # 3. Phân loại và Xử lý Payload
    block_type = data.get('type')
    raw_payload = data.get('payload', {})
    
    final_payload = raw_payload # Mặc định giữ nguyên
    quiz_ref_model = None
    files_to_commit = []

    # Map để lấy ID file nhanh cho các loại media đơn giản
    # Ví dụ: block type 'video' thì tìm key 'video_id' trong payload
    single_file_map = {
        'video': 'video_id',
        'pdf': 'file_id',
        'docx': 'file_id',
        'audio': 'audio_id', 
        'file': 'file_id',
    }

    # --- LOGIC ROUTER ---
    if block_type == 'quiz':
        # Delegate việc tạo Quiz sang service khác
        new_quiz_domain = create_quiz(data=raw_payload, actor=actor)
        
        # Link Quiz vừa tạo vào Block
        # Lưu ý: create_quiz trả về Domain, cần query lại Model hoặc dùng ID
        quiz_ref_model = Quiz.objects.get(id=new_quiz_domain.id)
        final_payload = {'quiz_id': str(new_quiz_domain.id)}

    elif block_type == 'rich_text':
        # Rich Text: Quét HTML để tìm các ảnh/file được nhúng
        html_text = raw_payload.get('html_content', '')
        files_to_commit.extend(_extract_file_ids_from_html(html_text))

    elif block_type in single_file_map:
        # Media Block: Lấy 1 file ID duy nhất
        key_name = single_file_map[block_type]
        file_val = raw_payload.get(key_name)
        if file_val:
            files_to_commit.append(file_val)

    # 4. Tạo ContentBlock trong DB
    new_block = ContentBlock.objects.create(
        lesson=lesson,
        type=block_type,
        payload=final_payload,
        position=position,
        quiz_ref=quiz_ref_model
    )

    # 5. Commit File (Nếu có)
    # Bước này quan trọng để chuyển trạng thái file từ 'pending' sang 'active'
    # và gắn chủ sở hữu là cái Block vừa tạo.
    if files_to_commit:
        commit_files_by_ids_for_object(
            file_ids=files_to_commit,
            related_object=new_block, 
            actor=actor
        )

    return ContentBlockDomain.from_model_detail(new_block)


# ==========================================
# PUBLIC INTERFACE (UPDATE)
# ==========================================

@transaction.atomic
def update_content_block(
    block_id: uuid.UUID, 
    data: dict, 
    actor: UserModel
) -> ContentBlockDomain:
    """
    Update content block.
    Quan trọng: Nếu payload thay đổi (vd: sửa bài viết, đổi video), 
    cần quét lại file ID để commit (chuyển trạng thái file thành permanent).
    """
    # 1. Tìm Block
    try:
        # Select related quiz_ref để lúc return domain có đủ data
        block = ContentBlock.objects.select_related('quiz_ref').get(id=block_id)
    except ContentBlock.DoesNotExist:
        raise DomainError(f"ContentBlock với ID '{block_id}' không tồn tại.")

    # 2. Update Basic Fields
    if 'title' in data:
        block.title = data['title']
    
    # 3. Update Payload & Xử lý File (Nếu có thay đổi payload)
    if 'payload' in data:
        incoming_payload = data['payload'] # Dữ liệu mới gửi lên
        current_payload = block.payload or {} # Dữ liệu đang có trong DB

        updated_payload = current_payload.copy()
        updated_payload.update(incoming_payload)

        block_type = block.type # Thường không cho đổi type khi update, giữ type cũ
        files_to_commit = []
        
        # Map logic giống hệt create
        single_file_map = {
            'video': 'video_id',
            'pdf': 'file_id',
            'docx': 'file_id',
            'audio': 'audio_id', 
            'file': 'file_id',
        }

        # --- LOGIC QUÉT FILE MỚI ---
        if block_type == 'rich_text':
            html_text = updated_payload.get('html_content', '')
            # Extract lại file từ HTML mới. 
            # Hàm commit_files_... thường là idempotent (chạy lại với file đã commit rồi cũng không sao)
            files_to_commit.extend(_extract_file_ids_from_html(html_text))

        elif block_type in single_file_map:
            key_name = single_file_map[block_type]
            file_val = incoming_payload.get(key_name)
            if file_val:
                files_to_commit.append(file_val)
        
        elif block_type == 'quiz':
            # Nếu payload có chứa quiz_id mới (trường hợp đổi đề thi khác)
            if 'quiz_id' in incoming_payload:
                try:
                    new_quiz = Quiz.objects.get(id=incoming_payload['quiz_id'])
                    block.quiz_ref = new_quiz
                except Quiz.DoesNotExist:
                    pass # Hoặc raise lỗi tùy business
        
        # Cập nhật payload vào DB
        block.payload = updated_payload

        # 4. Commit File Mới (Nếu có)
        if files_to_commit:
            commit_files_by_ids_for_object(
                file_ids=files_to_commit,
                related_object=block, 
                actor=actor
            )

    # 5. Save
    block.save()

    return ContentBlockDomain.from_model_detail(block)


# ==========================================
# PUBLIC INTERFACE (DELETE)
# ==========================================

@transaction.atomic
def delete_content_block(block_id: uuid.UUID) -> None:
    """
    Xóa content block.
    File đính kèm sẽ tự động được xử lý bởi GenericRelation hoặc logic dọn dẹp định kỳ.
    """
    try:
        block = ContentBlock.objects.get(id=block_id)
    except ContentBlock.DoesNotExist:
        # Nếu block không tồn tại, coi như đã xóa thành công (Idempotent)
        # Hoặc raise lỗi nếu muốn báo FE biết.
        raise DomainError(f"ContentBlock với ID '{block_id}' không tồn tại.")

    block.delete()


# ==========================================
# PUBLIC INTERFACE (CONVERT TYPE)
# ==========================================

@transaction.atomic
def convert_content_block(
    block_id: uuid.UUID, 
    target_type: str, 
    actor: UserModel
) -> ContentBlockDomain:
    """
    Chuyển đổi loại block (Ví dụ: Text -> Video).
    Logic: Xóa block cũ, tạo block mới cùng ID (hoặc ID mới) tại CÙNG VỊ TRÍ.
    """
    try:
        old_block = ContentBlock.objects.get(id=block_id)
    except ContentBlock.DoesNotExist:
        raise DomainError("Block không tồn tại.")

    if old_block.type == target_type:
        return ContentBlockDomain.from_model_detail(old_block)

    # 1. Lưu thông tin quan trọng
    saved_lesson = old_block.lesson
    saved_position = old_block.position
    saved_title = old_block.title
    
    # 2. Xóa block cũ (Dọn dẹp file cũ nếu có)
    old_block.delete()

    # 3. Chuẩn bị payload cho loại mới
    new_payload = {}
    new_quiz_ref = None

    if target_type == 'rich_text':
        new_payload = {'html_content': ''}

    elif target_type == 'quiz':
        # Tạo quiz mới tinh
        new_quiz_domain = create_quiz({'title': 'Untitled Quiz'}, actor=actor)

        try:
            new_quiz_ref = Quiz.objects.get(id=new_quiz_domain.id)
        except Quiz.DoesNotExist:
             raise ValueError("Lỗi hệ thống: Không tìm thấy Quiz vừa tạo.")

        new_payload = {'quiz_id': str(new_quiz_domain.id)}

    elif target_type in ['video', 'pdf', 'docx', 'audio', 'file']:
        # Media: Khởi tạo rỗng hoàn toàn. 
        # Frontend sẽ check: Nếu video_id null -> Hiện nút Upload.
        new_payload = {}

    # 4. Tạo block mới thế chỗ (The Swap)
    new_block = ContentBlock.objects.create(
        lesson=saved_lesson,
        type=target_type,
        title=saved_title, 
        position=saved_position, 
        payload=new_payload,
        quiz_ref=new_quiz_ref
    )

    return ContentBlockDomain.from_model_detail(new_block)


# ==========================================
# PUBLIC INTERFACE (REORDER)
# ==========================================

@transaction.atomic
def reorder_content_blocks(
    lesson_id: uuid.UUID, 
    block_id_list: list[str | uuid.UUID]
) -> list[ContentBlockDomain]:
    """
    Sắp xếp lại thứ tự các block trong 1 lesson.
    """
    # 1. Lấy tất cả block thuộc lesson này
    # Dùng in_bulk để lấy dictionary {uuid: object}
    blocks_dict = ContentBlock.objects.filter(lesson_id=lesson_id).in_bulk(field_name='id')
    
    existing_ids_set = set(blocks_dict.keys())

    # 2. Parse Input từ Frontend
    try:
        input_uuids = [lid if isinstance(lid, uuid.UUID) else uuid.UUID(str(lid)) for lid in block_id_list]
    except ValueError:
        raise DomainError("Danh sách ID block lỗi định dạng.")

    input_ids_set = set(input_uuids)

    # 3. Validation Tính Toàn Vẹn (Security Check)
    # Nếu số lượng lệch nhau -> Có thể FE gửi thiếu hoặc gửi trùng
    if len(input_uuids) != len(existing_ids_set):
        raise DomainError(
            f"Dữ liệu không đồng bộ. DB có {len(existing_ids_set)} blocks, "
            f"nhưng nhận được {len(input_uuids)}. Vui lòng reload trang."
        )

    # Nếu tập hợp ID không khớp -> Có thể chứa ID của lesson khác
    if input_ids_set != existing_ids_set:
        raise DomainError("Danh sách ID gửi lên không khớp với dữ liệu trong bài học này.")

    # 4. Logic Update Position
    update_list = []
    ordered_blocks = []

    for index, block_id in enumerate(input_uuids):
        block = blocks_dict[block_id]
        ordered_blocks.append(block)

        if block.position != index:
            block.position = index
            update_list.append(block)

    # 5. Bulk Update (1 Query duy nhất)
    if update_list:
        ContentBlock.objects.bulk_update(update_list, ['position'])

    # Trả về dạng Summary (nhẹ) để FE cập nhật lại list nếu cần
    return [ContentBlockDomain.from_model_summary(b) for b in ordered_blocks]


# def get_block_by_id(block_id: uuid.UUID) -> ContentBlockDomain:
#     """
#     Lấy một block theo ID.
#     (Tương tự get_user_by_id)
#     """
#     block_model = _get_block_model(block_id)
#     return ContentBlockDomain.from_model(block_model)


def patch_content_block(block_id: uuid.UUID, data: Dict[str, Any]) -> Tuple[ContentBlockDomain, List[str]]:
    """
    Cập nhật (PATCH) một ContentBlock theo logic "Router".
    """
    
    # 1. Lấy đối tượng gốc
    try:
        block = ContentBlock.objects.get(id=block_id)
    except ContentBlock.DoesNotExist:
        raise ValueError(f"ContentBlock with id {block_id} not found.")

    files_to_commit = []
    payload_data = data.get('payload') # Dữ liệu payload MỚI gửi lên
    
    # 2. Xử lý Payload (Logic Router)
    if block.type == 'quiz':
        # --- Hướng QUIZ ---
        if payload_data is not None:
            # Lấy ID của quiz hiện tại từ payload CŨ (đang lưu trong DB)
            current_quiz_id_str = block.payload.get('quiz_id')
            if not current_quiz_id_str:
                raise ValueError("ContentBlock 'quiz' bị lỗi, không có 'quiz_id' trong payload.")
            
            # Ủy quyền cho service CSDL
            updated_quiz_model = patch_quiz(
                quiz_id=uuid.UUID(current_quiz_id_str),
                data=payload_data # Gửi DTO patch (title, questions: [...])
            )
            # (patch_quiz cũng nên trả về files_to_commit)

    else:
        # --- Hướng BLOCK THƯỜNG ---
        if payload_data is not None:
            # 2a. Ghi đè payload
            block.payload = payload_data
            
            # 2b. Thu thập file MỚI (nếu 'payload' được cập nhật)
            block_type = data.get('type', block.type) # Lấy type mới hoặc cũ
            url_key = None
            if block_type == 'image':
                url_key = 'image_id'
            elif block_type == 'video':
                url_key = 'video_id' # Sửa theo JSON create của bạn
            elif block_type in ['pdf', 'docx']:
                url_key = 'file_id'
            
            if url_key and url_key in payload_data:
                files_to_commit.append(payload_data[url_key])
        
    # 3. Cập nhật các trường chung (ngoài payload)
    if 'position' in data:
        block.position = data['position']
    
    # Cẩn thận khi cho phép đổi 'type' của block đã tồn tại
    if 'type' in data and block.type != 'quiz': 
        block.type = data['type']
        
    block.save() # Lưu tất cả thay đổi
            
    # 4. Trả về
    return ContentBlockDomain.from_model(block), files_to_commit


# @transaction.atomic
# def delete_block(block_id: uuid.UUID) -> None:
#     """
#     Xóa một content block và cập nhật lại position của các block sau nó.
#     (Tương tự delete_user, nhưng có thêm logic)
#     """
#     block_model = _get_block_model(block_id)
    
#     lesson_version = block_model.lesson_version
#     deleted_position = block_model.position

#     # 1. Xóa block
#     block_model.delete()
    
#     # 2. Business Logic: Cập nhật lại position
#     # Dồn các block ở vị trí sau lên 1 bậc (position - 1)
#     ContentBlock.objects.filter(
#         lesson_version=lesson_version,
#         position__gt=deleted_position
#     ).update(position=F('position') - 1)


# @transaction.atomic
# def reorder_blocks(lesson_id: uuid.UUID, ordered_ids: List[str]) -> None:
#     """
#     Sắp xếp lại vị trí của tất cả các block trong một version.
#     (Tương tự synchronize_roles ở khía cạnh bulk update)
#     """
#     version_model = _get_lesson_model(lesson_id)
    
#     # Lấy tất cả block hiện tại
#     blocks = ContentBlock.objects.filter(lesson_version=version_model)
#     block_map = {str(block.id): block for block in blocks}
    
#     # --- Business Logic: Validate input ---
#     current_ids = set(block_map.keys())
#     new_ids = set(ordered_ids)
    
#     if current_ids != new_ids:
#         raise BlockMismatchError(
#             "The list of IDs provided does not match the blocks for this version."
#         )

#     # Cập nhật position mới
#     update_list = []
#     for i, block_id_str in enumerate(ordered_ids):
#         block = block_map.get(block_id_str)
        
#         # Chỉ update nếu position thực sự thay đổi
#         if block and block.position != i:
#             block.position = i
#             update_list.append(block)
    
#     # Dùng bulk_update để tối ưu performance (1 query)
#     if update_list:
#         ContentBlock.objects.bulk_update(update_list, ['position'])

