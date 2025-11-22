import logging
import uuid
import os
import mimetypes
import magic
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseForbidden, FileResponse
from django.shortcuts import get_object_or_404
from django.utils.encoding import escape_uri_path # Cần cái này để xử lý tiếng Việt
from django.core.exceptions import ValidationError
from django.db import DatabaseError

from core.exceptions import DomainError, UserNotFoundError
from custom_account.models import UserModel
from content.models import Course, Lesson, Enrollment
from media.models import UploadedFile, FileStatus
from media.domains.file_domain import FileDomain



User = get_user_model()

@transaction.atomic
def create_file_upload(user: UserModel, data: dict) -> FileDomain:
    """
    Service xử lý nghiệp vụ upload file.
    Nhận user_id (từ request.user) và data (từ Pydantic Input DTO).
    
    QUAN TRỌNG: Trả về Model Instance (UploadedFile) 
    để RoleBasedOutputMixin có thể đọc attributes và @property.
    """
    
    # Giải nén dữ liệu từ dict
    file_data = data.get('file')
    content_type_str = data.get('content_type_str')
    object_id = data.get('object_id')
    component = data.get('component')

    if not all([file_data, content_type_str, component is not None]):
        raise DomainError("Dữ liệu input (file, content_type, component) bị thiếu.")
    
    if content_type_str and object_id is not None:
        try:
            app_label, model_name = content_type_str.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        except (ContentType.DoesNotExist, ValueError, AttributeError):
            raise DomainError(f"Content_type không hợp lệ: '{content_type_str}'.")

        try:
            ParentModel = content_type.model_class()
            if not ParentModel.objects.filter(pk=object_id).exists():
                raise DomainError(f"Không tìm thấy đối tượng '{content_type_str}' với ID {object_id}.")
        except Exception as e:
            raise DomainError(f"Lỗi khi kiểm tra đối tượng cha: {e}")
    else:
        content_type = None

    # --- NEW: LOGIC TÍNH MIME TYPE ---
    # 1. Ưu tiên lấy từ header file mà trình duyệt gửi lên (file_data.content_type)
    #    Đây là cách nhanh nhất vì file đang nằm trong RAM/Temp
    mime_type = getattr(file_data, 'content_type', None)

    # 2. Nếu không có, dùng mimetypes đoán qua tên file (fallback an toàn)
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(file_data.name)
    
    # 3. Nếu vẫn không ra, đặt mặc định
    if not mime_type:
        mime_type = 'application/octet-stream'

    saved_file_model = UploadedFile.objects.create(
        file=file_data,
        original_filename=file_data.name,
        uploaded_by=user,
        content_type=content_type,
        object_id=object_id,
        component=component,
        status=FileStatus.STAGING,

        mime_type=mime_type
    )
    
    return FileDomain.from_model(saved_file_model)


@transaction.atomic
def commit_files_by_ids_for_object(file_ids: list[str], related_object, actor: AbstractBaseUser = None) -> int:
    logger.info(f"Bắt đầu commit file (bằng ID) cho đối tượng {related_object}...")

    if not file_ids:
        logger.warning("Không có ID file nào được cung cấp để commit.")
        return 0

    # 1. VALIDATE & CHUẨN HÓA UUID
    valid_target_ids = set()
    for fid in file_ids:
        try:
            # Kiểm tra xem string có phải UUID hợp lệ không
            uuid_obj = uuid.UUID(str(fid))
            valid_target_ids.add(str(uuid_obj))
        except (ValueError, TypeError):
            # Nếu ID rác -> Bỏ qua hoặc Báo lỗi tùy nghiệp vụ. 
            # Ở đây ta chọn báo lỗi để Frontend biết đường sửa.
            msg = f"ID file không hợp lệ: {fid}"
            logger.warning(msg)
            raise DomainError(msg)

    # 2. Lấy ContentType (Giữ nguyên)
    try:
        content_type = ContentType.objects.get_for_model(related_object)
        object_id = str(related_object.pk)
    except Exception as e:
        logger.error(f"Lỗi khi lấy ContentType: {e}", exc_info=True)
        raise DomainError(f"Không thể lấy ContentType cho {related_object}")

    # 3. TRUY VẤN DB (AN TOÀN CẤP ĐỘ CAO)
    # Lấy owner của related_object (nếu có) để đảm bảo chính chủ
    # Hầu hết các model trong LMS (Course, Lesson) đều có field 'owner' hoặc 'created_by'
    owner = getattr(related_object, 'owner', None) 
    
    is_admin=False
    if actor and (getattr(actor, 'is_staff', False) or getattr(actor, 'is_superuser', False)):
        is_admin = True

    filters = Q(id__in=valid_target_ids)
    
    # Điều kiện 1: File đã thuộc về Object này rồi (Re-save)
    cond_owned_by_object = Q(content_type=content_type, object_id=object_id)
    
    # Điều kiện 2: HOẶC File mới (Pending) VÀ phải do chính người này upload
    staging_files_condition = Q(status=FileStatus.STAGING)
    
    # --- LOGIC PHÂN QUYỀN QUAN TRỌNG ---
    if not is_admin:
        # USER THƯỜNG:
        # Chỉ được commit file staging nếu file đó do CHÍNH CHỦ sở hữu object upload
        # (Hoặc do chính actor upload - tùy nghiệp vụ bạn muốn chặt đến đâu)
        if owner:
            staging_files_condition &= Q(uploaded_by=owner)
        else:
            # Nếu object không có owner (trường hợp hiếm), bắt buộc file phải do actor upload
            if actor:
                staging_files_condition &= Q(uploaded_by=actor)
    else:
        # ADMIN:
        # Được phép commit BẤT KỲ file staging nào (miễn là có ID).
        # Admin có quyền tối thượng ("God mode") để sửa chữa dữ liệu hộ user.
        pass

    # Combine
    files_qs = UploadedFile.objects.filter(
        filters & (staging_files_condition | cond_owned_by_object)
    )
    
    # Lấy ra các object thực tế từ DB
    files_in_db = list(files_qs) # Query 1 lần ra list object
    
    # Tạo dict để map ID -> Object cho dễ truy xuất
    files_map = {str(f.id): f for f in files_in_db}
    
    # Lấy ra danh sách các ID thực sự tìm thấy trong DB
    # values_list trả về UUID object, nên cần ép kiểu str để so sánh với target_ids
    found_ids = set(str(uid) for uid in files_qs.values_list('id', flat=True))
    

    # 4. KIỂM TRA THIẾU (MISSING OR FORBIDDEN)
    # missing_ids ở đây bao gồm cả: File không tồn tại VÀ File tồn tại nhưng của người khác
    missing_ids = valid_target_ids - found_ids

    if missing_ids:
        error_msg = (
            f"Không thể commit các file sau (Không tồn tại hoặc thuộc về đối tượng khác): "
            f"{missing_ids}"
        )
        logger.error(error_msg)
        # Bắn lỗi ngay lập tức, transaction sẽ rollback
        raise DomainError(error_msg)

    update_list = []
    
    # Lặp theo danh sách file_ids GỐC (để giữ thứ tự)
    for index, fid_str in enumerate(file_ids):
        if fid_str in files_map:
            file_obj = files_map[fid_str]
            
            # Cập nhật thông tin commit
            file_obj.status = FileStatus.COMMITTED
            file_obj.content_type = content_type
            file_obj.object_id = object_id
            
            # QUAN TRỌNG: Lưu thứ tự từ input vào DB
            file_obj.sort_order = index 
            
            update_list.append(file_obj)
    
    if update_list:
        # Dùng bulk_update để tối ưu (chỉ 1 query update thay vì N query)
        # Cập nhật cả status, thông tin relation và sort_order
        UploadedFile.objects.bulk_update(
            update_list, 
            ['status', 'content_type', 'object_id', 'sort_order']
        )

    logger.info(f"Đã commit và sắp xếp thành công {len(update_list)} file.")
    
    return len(update_list)


logger = logging.getLogger(__name__)

@transaction.atomic
def cleanup_staging_files(days_old: int) -> dict:
    """
    Dọn dẹp các file 'staging' cũ hơn N ngày.
    Đây là tác vụ chính, chạy nhanh vì chỉ query CSDL.
    """
    if days_old <= 0:
        raise ValueError("Số ngày phải lớn hơn 0")

    # 1. Tính toán mốc thời gian
    cutoff_time = timezone.now() - timedelta(days=days_old)
    
    logger.info(f"Bắt đầu dọn dẹp file staging cũ hơn {cutoff_time}...")

    # 2. Tìm tất cả các file "mồ côi"
    orphan_files = UploadedFile.objects.filter(
        status=FileStatus.STAGING,
        uploaded_at__lt=cutoff_time
    )

    count = orphan_files.count()
    if count == 0:
        return {"deleted_count": 0, "filenames": []}

    # 3. Lặp và xóa (để kích hoạt xóa file vật lý)
    deleted_filenames = []
    for file_record in orphan_files.iterator(): # Dùng iterator() cho hiệu quả
        try:
            file_name = file_record.file.name
            
            # Quan trọng: Xóa file vật lý khỏi S3/thư mục media
            file_record.file.delete(save=False) 
            
            # Xóa bản ghi (record) khỏi CSDL
            file_record.delete()
            
            deleted_filenames.append(file_name)
        except Exception as e:
            # Ghi log nếu xóa 1 file lỗi, nhưng vẫn tiếp tục
            logger.error(f"Lỗi khi xóa file {file_record.id} ({file_name}): {e}", exc_info=True)

    logger.info(f"Đã dọn dẹp thành công {len(deleted_filenames)} file.")
    
    return {
        "deleted_count": len(deleted_filenames),
        "filenames": deleted_filenames
    }


@transaction.atomic
def cleanup_broken_links() -> dict:
    """
    Dọn dẹp các bản ghi CSDL mà file vật lý không còn tồn tại.
    
    !!! CẢNH BÁO: TÁC VỤ NÀY RẤT CHẬM !!!
    Nó phải gọi API (S3, v.v.) để kiểm tra TỪNG FILE.
    Không nên chạy qua API View, mà nên chạy bằng Management Command.
    """
    logger.warning("Bắt đầu quét file hỏng (tác vụ chậm)...")
    broken_files = []
    
    # Lặp qua TẤT CẢ các file, bất kể status
    for file_record in UploadedFile.objects.all().iterator():
        
        # 1. Nếu file field bị rỗng (lỗi data)
        if not file_record.file:
            logger.warning(f"Bản ghi {file_record.id} không có file. Đang xóa...")
            broken_files.append(f"Record_ID_{file_record.id}_missing_file_field")
            file_record.delete()
            continue
            
        # 2. Nếu file không tồn tại trên storage (S3, local, v.v.)
        if not default_storage.exists(file_record.file.name):
            logger.warning(f"File {file_record.file.name} (ID: {file_record.id}) không tồn tại. Đang xóa...")
            broken_files.append(file_record.file.name)
            
            # Chỉ xóa bản ghi CSDL, file vật lý đã mất rồi
            file_record.delete()
            
    logger.info(f"Đã dọn dẹp {len(broken_files)} file hỏng.")
    return {
        "deleted_count": len(broken_files),
        "filenames": broken_files
    }

def list_all_files() -> list[FileDomain]: # <-- Thay đổi ở đây
        """
        Lấy một QuerySet của TẤT CẢ các file,
        sắp xếp theo ngày mới nhất.
        
        """
        logger.info("Service: Lấy danh sách tất cả file và chuyển sang Domain.")
        
        # Lấy tất cả model từ CSDL 
        all_file_models = UploadedFile.objects.select_related(
            'uploaded_by'
        ).all().order_by('-uploaded_at')

        # Chuyển đổi QuerySet[Model] -> list[Domain]
        all_file_domains = [
            FileDomain.from_model(model) for model in all_file_models
        ]
        
        # 3. Trả về list các domain object
        return all_file_domains


def get_file_model(file_id: uuid.UUID) -> UploadedFile:
        """Hàm helper nội bộ để lấy model (tránh lặp code)."""
        try:
            return UploadedFile.objects.get(pk=file_id)
        except UploadedFile.DoesNotExist:
          
            raise FileNotFoundError(f"Không tìm thấy file với ID: {file_id}")


def get_file_by_id(file_id: uuid.UUID) -> FileDomain:
    """
    Lấy một file cụ thể bằng ID và trả về domain object.
    """
    logger.info(f"Service: Lấy file ID {file_id}...")
    
    file_model = get_file_model(file_id)
    
    # Dùng lại from_model (đã có 'url' attribute)
    return FileDomain.from_model(file_model)


def update_file(file_id: uuid.UUID, data: dict) -> FileDomain:
    """
    Cập nhật một phần (PATCH) file record.
    'data' là một dict chỉ chứa các trường cần thay đổi.
    """
    logger.info(f"Service: Cập nhật file ID {file_id} với data: {data}")
    
    file_model = get_file_model(file_id)
    
    # Cập nhật các trường từ dict
    # Ví dụ: data = {"status": "committed", "component": "new_component"}
    has_changed = False
    for field, value in data.items():
        if hasattr(file_model, field):
            setattr(file_model, field, value)
            has_changed = True
    
    if has_changed:
        # Chỉ lưu các trường đã thay đổi
        file_model.save(update_fields=data.keys())
    
    return FileDomain.from_model(file_model)


def delete_file(file_id: uuid.UUID) -> None:
    """
    Service xóa file lẻ (Dành cho API xóa file độc lập).
    """
    logger.info(f"Service: Yêu cầu xóa file ID {file_id}...")
    
    # 1. Tìm file
    try:
        file_model = UploadedFile.objects.get(pk=file_id)
    except UploadedFile.DoesNotExist:
        # Nếu file không tồn tại, coi như đã xóa thành công (Idempotent)
        return None

    # 2. Chỉ cần gọi delete() của Model
    # Signal post_delete sẽ tự động nhảy vào xóa file trên S3/Disk
    file_model.delete()
    
    logger.info(f"Service: Đã xóa file ID {file_id}.")
    return None


def user_has_access_to_file(user: UserModel, file_object: UploadedFile) -> bool:
    """
    Kiểm tra xem user có quyền truy cập file này không (phiên bản đầy đủ).
    Bao gồm: Admin, Owner (Giảng viên), Enrolled User (Học viên),
    và các khóa học Public.
    """
    
    # 0. Admin/Staff luôn có quyền
    # (Bỏ qua nếu bạn không muốn staff có toàn quyền)
    if user.is_superuser or user.is_staff:
        return True
        
    try:
        # 1. Lấy đối tượng mà file này được đính kèm (Course, Lesson, v.v.)
        related_object = file_object.content_object 
        
        if related_object is None:
            # File 'staging' hoặc bị lỗi (chưa commit), không ai được xem
            return False

        # 2. Xác định khóa học (Course) liên quan
        #    Chúng ta cần tìm ra khóa học "cha" chứa file này
        course_to_check = None

        if isinstance(related_object, Course):
            # File này là ảnh bìa của chính khóa học
            course_to_check = related_object

        elif isinstance(related_object, Lesson):
            # File này là tài liệu của một bài giảng
            # Phải truy ngược lên để tìm Course
            course_to_check = related_object.module.course 
        
        # (Bạn có thể thêm 'elif' cho ContentBlock nếu file đính kèm vào đó)
        # elif isinstance(related_object, ContentBlock):
        #    course_to_check = related_object.lesson.module.course

        # 3. Bắt đầu kiểm tra quyền trên khóa học (course_to_check)
        if course_to_check:
            
            # LOGIC 1: Khóa học có công khai (public) không?
            # (Giả sử bạn có trường 'published' hoặc 'is_public' trên Course)
            if course_to_check.published: # Hoặc .is_public
                # Nếu khóa học đã public, ai cũng được xem file (kể cả user vãng lai)
                # Bạn có thể bỏ qua check này nếu muốn khóa học public
                # nhưng tài liệu vẫn phải đăng nhập
                return True 

            # LOGIC 2: User có phải là chủ khóa học (Giảng viên) không?
            if course_to_check.owner == user:
                return True

            # LOGIC 3: User có phải là học viên đã ghi danh (Enrolled) không?
            # ĐÂY CHÍNH LÀ PHẦN BẠN CẦN!
            # (Giả sử bạn có model Enrollment liên kết User và Course)
            if Enrollment.objects.filter(course=course_to_check, user=user, is_active=True).exists():
                return True

        # 4. Mặc định là KHÔNG
        # Nếu không rơi vào 3 logic trên, user không có quyền
        return False
        
    except Exception as e:
        # Ghi log lỗi nếu cần
        # logger.error(f"Lỗi nghiêm trọng khi kiểm tra quyền file {file_object.id} cho user {user.id}: {e}")
        return False
    

def _get_best_mime_type(file_obj):
    """
    Hàm ưu tiên lấy từ DB, nếu không có thì đoán.
    """
    # Ưu tiên 1: Lấy từ DB (Nhanh nhất - O(1))
    # Vì bạn mới thêm trường này, nên các file cũ có thể là Null/None
    if file_obj.mime_type:
        return str(file_obj.mime_type)

    # Ưu tiên 2: Đoán từ tên file gốc (Nhanh nhì)
    # VD: 'bai_giang.mp4' -> 'video/mp4'
    guessed_type, _ = mimetypes.guess_type(file_obj.original_filename or file_obj.file.name)
    if guessed_type:
        return guessed_type

    # Ưu tiên 3: Mặc định an toàn (Binary)
    return 'application/octet-stream'

def _is_browser_viewable(mime_type):
    """
    Danh sách các loại file trình duyệt có thể mở được ngay
    """
    if not mime_type: return False
    
    viewable_types = [
        'application/pdf',
        'video/mp4', 'video/webm', 'video/ogg',
        'audio/mpeg', 'audio/ogg', 'audio/wav',
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
        'text/plain'
    ]
    return mime_type in viewable_types


def serve_file(request, file_id, user):
    """
    Xử lý logic check quyền và trả về file response.
    """
    # 1. Lấy object (Nên cache nhẹ chỗ này nếu lượng truy cập lớn)
    try:
        file_obj = get_object_or_404(UploadedFile, id=file_id)
    except ValidationError:
        raise ValidationError("File ID không đúng định dạng UUID.")
    except DatabaseError:
        # Lỗi mất kết nối DB
        raise DatabaseError("Lỗi kết nối cơ sở dữ liệu.")

    # 2. Check quyền (Logic nghiệp vụ)
    # Giả sử bạn có service check quyền riêng
    if not user_has_access_to_file(user=user, file_object=file_obj):
        return PermissionError("Bạn không có quyền truy cập tài nguyên này.")

    # 3. BẮT LỖI FILE VẬT LÝ (IO Error)
    if not file_obj.file:
        # Trường hợp DB có record nhưng trường file bị null
        raise FileNotFoundError(f"Dữ liệu file bị thiếu trong Database (ID: {file_id}).")
        
    if not os.path.exists(file_obj.file.path):
        # Trường hợp file bị xóa khỏi ổ cứng
        raise FileNotFoundError(f"File gốc không tồn tại trên ổ đĩa: {file_obj.file.path}")

    # 4. XÁC ĐỊNH MIME TYPE (Logic quan trọng nhất)
    real_mime_type = _get_best_mime_type(file_obj=file_obj)

    # 5. Xử lý hiển thị (Inline vs Attachment)
    # Inline: Xem trực tiếp trên trình duyệt (Video, Ảnh, PDF)
    # Attachment: Tải về (Zip, Docx, Exe)
    disposition_type = 'inline' if _is_browser_viewable(real_mime_type) else 'attachment'

    # 5. XỬ LÝ TÊN FILE TIẾNG VIỆT (Chống lỗi UnicodeEncodeError)
    # Cách chuẩn RFC 5987: filename*=UTF-8''ten_file_ma_hoa
    safe_filename = escape_uri_path(file_obj.original_filename)

    # --- TRẢ VỀ RESPONSE ---

    # A. DEV MODE
    if settings.DEBUG:
        try:
            f = open(file_obj.file.path, 'rb')
            response = FileResponse(f, content_type=real_mime_type)
        except PermissionError:
            raise PermissionError("Server không có quyền đọc file này (Permission Denied từ OS).")
        except OSError as e:
            raise OSError(f"Lỗi IO khi mở file: {str(e)}")

    # B. PRODUCTION MODE (Nginx)
    else:
        response = HttpResponse()
        nginx_path = f"/protected_media/{file_obj.file.name}"
        response['X-Accel-Redirect'] = nginx_path
        response['Content-Type'] = real_mime_type

    # Thiết lập Header an toàn cho tiếng Việt
    # Thay vì: filename="tên tiếng việt.mp4" (Gây lỗi)
    # Dùng: filename*=UTF-8''t%C3%AAn%20ti%E1%BA%BFng%20vi%E1%BB%87t.mp4
    response['Content-Disposition'] = f"{disposition_type}; filename*=UTF-8''{safe_filename}"
    
    return response