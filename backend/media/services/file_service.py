import logging
import magic
import mimetypes
import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.exceptions import DomainError, FileNotFoundError
from custom_account.models import UserModel
from quiz.models import QuizAttempt
from content.models import Course, Enrollment
from media.models import UploadedFile, FileStatus, Component
from media.domains.file_domain import FileDomain



User = get_user_model()

# django-storages sẽ tự động chặn việc lưu local và đẩy thẳng lên S3 
# khi lệnh UploadedFile.objects.create chạy.
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
    
    # Lấy kích thước file (byte)
    file_size = getattr(file_data, 'size', 0)

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        # Đổi ra MB để báo lỗi cho thân thiện
        size_in_mb = round(file_size / (1024 * 1024), 2)
        raise DomainError(
            f"File quá lớn ({size_in_mb}MB). Giới hạn tối đa là {settings.MAX_FILE_SIZE_MB}MB."
        )

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

    # --- [MỚI] LOGIC LẤY FILE SIZE ---
    # file_data.size trả về kích thước bằng byte (int)
    file_size = getattr(file_data, 'size', 0)

    saved_file_model = UploadedFile.objects.create(
        file=file_data,
        original_filename=file_data.name,
        uploaded_by=user,
        content_type=content_type,
        object_id=object_id,
        component=component,
        status=FileStatus.STAGING,

        mime_type=mime_type,
        file_size=file_size
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
        raise DomainError(f"Không thể lấy ContentType cho {related_object}: {e}")

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


# @transaction.atomic
# def cleanup_broken_links() -> dict:
#     """
#     Dọn dẹp các bản ghi CSDL mà file vật lý không còn tồn tại.
    
#     !!! CẢNH BÁO: TÁC VỤ NÀY RẤT CHẬM !!!
#     Nó phải gọi API (S3, v.v.) để kiểm tra TỪNG FILE.
#     Không nên chạy qua API View, mà nên chạy bằng Management Command.
#     """
#     logger.warning("Bắt đầu quét file hỏng (tác vụ chậm)...")
#     broken_files = []
    
#     # Lặp qua TẤT CẢ các file, bất kể status
#     for file_record in UploadedFile.objects.all().iterator():
        
#         # 1. Nếu file field bị rỗng (lỗi data)
#         if not file_record.file:
#             logger.warning(f"Bản ghi {file_record.id} không có file. Đang xóa...")
#             broken_files.append(f"Record_ID_{file_record.id}_missing_file_field")
#             file_record.delete()
#             continue
            
#         # 2. Nếu file không tồn tại trên storage (S3, local, v.v.)
#         if not default_storage.exists(file_record.file.name):
#             logger.warning(f"File {file_record.file.name} (ID: {file_record.id}) không tồn tại. Đang xóa...")
#             broken_files.append(file_record.file.name)
            
#             # Chỉ xóa bản ghi CSDL, file vật lý đã mất rồi
#             file_record.delete()
            
#     logger.info(f"Đã dọn dẹp {len(broken_files)} file hỏng.")
#     return {
#         "deleted_count": len(broken_files),
#         "filenames": broken_files
#     }


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


def _check_quiz_access(user, related_object):
    # ... (Logic quiz như cũ của bạn) ...
    # Tìm Quiz cha
    quiz = related_object.quiz if hasattr(related_object, 'quiz') else related_object
    
    if quiz.mode == 'practice':
        return True
    
    # Check Attempt
    return QuizAttempt.objects.filter(user=user, quiz=quiz).exists()


def _get_course_from_object(obj):
    """Hàm đệ quy hoặc if/else để tìm Course từ Lesson/Block"""
    if obj._meta.model_name == 'course':
        return obj
    if hasattr(obj, 'course'): # Quan hệ trực tiếp
        return obj.course
    if hasattr(obj, 'module') and hasattr(obj.module, 'course'): # Lesson -> Module -> Course
        return obj.module.course
    return None


def user_is_enrolled(user, course: Course) -> bool:
    """
    Kiểm tra xem user có đang ghi danh vào khóa học này không.
    """
    # 2. Check trong bảng Enrollment
    # Dùng .exists() là tối ưu nhất vì nó không load dữ liệu lên RAM, 
    # chỉ trả về True/False ở cấp DB.
    return Enrollment.objects.filter(
        user=user, 
        course=course
    ).exists()


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
    
    PUBLIC_COMPONENTS = {
        Component.COURSE_THUMBNAIL,
        Component.USER_AVATAR,
        Component.SITE_LOGO,
        Component.PUBLIC_ATTACHMENT
    }
    
    if file_object.component in PUBLIC_COMPONENTS:
        return True

    # =========================================================
    # NẾU KHÔNG PHẢI PUBLIC, BẮT ĐẦU CHECK NGHIỆP VỤ SÂU HƠN
    # =========================================================

    # # Lấy đối tượng cha (Course, Lesson, Quiz...)
    related_object = file_object.content_object
    if not related_object:
        return False # File mồ côi (chưa gắn vào đâu) -> Chặn

    owner_id = getattr(related_object, 'owner_id', None)
    course = None

    # Case 1: Đối tượng nằm trong Quiz (Câu hỏi, Ảnh đề bài)
    # (Ưu tiên check Quiz trước vì Question thường không nối trực tiếp Course)
    if hasattr(related_object, 'quiz'): 
        quiz = related_object.quiz
        owner_id = getattr(quiz, 'owner_id', owner_id)

    # Case 2: Đối tượng nằm trong Course (Bài học, Tài liệu)
    elif hasattr(related_object, 'course'):
        course = related_object.course
        owner_id = getattr(course, 'owner_id', owner_id)

    # Case 3: Fallback (Dùng helper nếu logic phức tạp hơn)
    if not course:
        # Hàm này bạn đã có, tái sử dụng nó
        course = _get_course_from_object(related_object) 
        if course and not owner_id:
             owner_id = getattr(course, 'owner_id', None)

    if owner_id and str(owner_id) == str(user.id):
        return True
    
    if file_object.component == Component.QUIZ_ATTACHMENT:
        return _check_quiz_access(user, related_object)

    if course:
        # Nếu Course Public -> Cho xem
        if getattr(course, 'is_public', False):
            return True
            
        # Nếu User đã Enroll -> Cho xem
        if user_is_enrolled(user, course):
            return True
        
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
    Service trả về URL để user tải/xem file từ S3.
    """
    # 1. Lấy object
    try:
        file_obj = get_object_or_404(UploadedFile, id=file_id)
    except UploadedFile.DoesNotExist:
        raise FileNotFoundError(f"File {file_id} không tồn tại trong hệ thống.")

    # 2. Check quyền (Logic nghiệp vụ giữ nguyên)
    if not user_has_access_to_file(user=user, file_object=file_obj):
        # Lưu ý: Raise exception để Middleware bắt hoặc return response lỗi
        # Tùy architecture của bạn, ở đây giả sử return response
        return PermissionDenied("Bạn không có quyền truy cập tài nguyên này.")

    # 3. KHÔNG CHECK os.path.exists
    # Với S3, việc check tồn tại tốn 1 request mạng. 
    # Ta tin tưởng vào Database. Nếu DB có mà S3 mất thì S3 sẽ báo lỗi 404 sau.
    if not file_obj.file:
         raise FileNotFoundError("Dữ liệu file bị thiếu trong Database.")

    # 4. Xử lý logic hiển thị (Download vs Inline) & Tên file tiếng Việt
    # Logic cũ của bạn set header trên Response, nhưng với S3,
    # ta phải bảo S3 set header đó thông qua query params của URL.
    
    # Xác định xem nên xem ngay hay tải về
    real_mime_type = file_obj.mime_type or 'application/octet-stream'
    disposition_type = 'inline' if _is_browser_viewable(real_mime_type) else 'attachment'
    
    # Xử lý tên file (filename)
    # Với S3 presigned url, tham số ResponseContentDisposition sẽ quyết định header trả về
    filename = file_obj.original_filename
    
    # Chuẩn bị tham số cho hàm generate URL của django-storages
    # Lưu ý: "ResponseContentDisposition" là tham số chuẩn của S3
    response_headers = {
        'ResponseContentType': real_mime_type,
        'ResponseContentDisposition': f'{disposition_type}; filename="{filename}"' 
        # S3 tự xử lý unicode filename khá tốt, nhưng nếu cần kỹ hơn có thể encode
    }

    # 5. SINH URL VÀ REDIRECT
    try:
        # file_obj.file.url bản chất sẽ gọi S3 API để sinh Presigned URL
        # Nếu dùng django-storages, có thể truyền parameters vào (tùy version)
        # Cách đơn giản nhất (mặc định):
        s3_url = file_obj.file.url
        
        # NẾU CẦN CUSTOM HEADER (như tên file tải về), 
        # bạn cần can thiệp sâu hơn vào storage backend hoặc cấu hình AWS_S3_OBJECT_PARAMETERS.
        # Nhưng ở mức cơ bản, chỉ cần redirect là đủ:
    
        return s3_url

    except Exception as e:
        # Phòng trường hợp mất kết nối AWS hoặc lỗi config
        print(f"S3 Error: {e}")
        raise OSError(f"Không thể kết nối đến hệ thống lưu trữ - {str(e)}")


# def serve_file_in_local(request, file_id, user):
#     """
#     Xử lý logic check quyền và trả về file response.
#     """
#     # 1. Lấy object (Nên cache nhẹ chỗ này nếu lượng truy cập lớn)
#     try:
#         file_obj = get_object_or_404(UploadedFile, id=file_id)
#     except UploadedFile.DoesNotExist:
#         raise FileNotFoundError("File không tồn tại trong hệ thống.")


#     # 2. Check quyền (Logic nghiệp vụ)
#     # Giả sử bạn có service check quyền riêng
#     if not user_has_access_to_file(user=user, file_object=file_obj):
#         raise AccessDeniedError("Bạn không có quyền truy cập tài nguyên này.")

#     # 3. BẮT LỖI FILE VẬT LÝ (IO Error)
#     if not file_obj.file:
#         # Trường hợp DB có record nhưng trường file bị null
#         raise FileNotFoundError(f"Dữ liệu file bị thiếu trong Database (ID: {file_id}).")
        
#     if not os.path.exists(file_obj.file.path):
#         # Trường hợp file bị xóa khỏi ổ cứng
#         raise FileNotFoundError(f"File gốc không tồn tại trên ổ đĩa: {file_obj.file.path}")

#     # 4. XÁC ĐỊNH MIME TYPE (Logic quan trọng nhất)
#     real_mime_type = _get_best_mime_type(file_obj=file_obj)

#     # --- TRẢ VỀ RESPONSE ---
#     print(f"DEBUG STATUS: {settings.DEBUG}")

#     # A. DEV MODE
#     if settings.DEBUG:
#         try:
#             # CÁCH FIX: Dùng file.open() thay vì open()
#             # Điều này giúp Django tự quản lý việc đóng mở file tốt hơn
#             file_handle = file_obj.file.open('rb') 
            
#             response = FileResponse(file_handle, content_type=real_mime_type)
            
#             # Thêm Content-Length để Client biết file nặng bao nhiêu mà hứng
#             if file_obj.file_size:
#                 response['Content-Length'] = file_obj.file_size
                
#             return response
            
#         except FileNotFoundError:
#             raise Http404("File gốc không tìm thấy trên ổ cứng.")
#         except Exception as e:
#             # In lỗi ra để debug nếu có lỗi khác
#             print(f"ERROR serving file: {e}")
#             raise OSError(f"Lỗi khi đọc file: {str(e)}")

#     # B. PRODUCTION MODE (Nginx)
#     else:
#         response = HttpResponse()
#         nginx_path = f"/protected_media/{file_obj.file.name}"
#         response['X-Accel-Redirect'] = nginx_path
#         response['Content-Type'] = real_mime_type

#         # Tối ưu: Giúp Nginx không phải tính lại dung lượng lần nữa
#         response['Content-Length'] = file_obj.file_size

#         # 5. Xử lý hiển thị (Inline vs Attachment)
#         # Inline: Xem trực tiếp trên trình duyệt (Video, Ảnh, PDF)
#         # Attachment: Tải về (Zip, Docx, Exe)
#         disposition_type = 'inline' if _is_browser_viewable(real_mime_type) else 'attachment'

#         # 5. XỬ LÝ TÊN FILE TIẾNG VIỆT (Chống lỗi UnicodeEncodeError)
#         # Cách chuẩn RFC 5987: filename*=UTF-8''ten_file_ma_hoa
#         safe_filename = escape_uri_path(file_obj.original_filename)

#         # Thiết lập Header an toàn cho tiếng Việt
#         # Thay vì: filename="tên tiếng việt.mp4" (Gây lỗi)
#         # Dùng: filename*=UTF-8''t%C3%AAn%20ti%E1%BA%BFng%20vi%E1%BB%87t.mp4
#         response['Content-Disposition'] = f"{disposition_type}; filename*=UTF-8''{safe_filename}"
    
#     return response