import base64
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import logging
import json
import magic
import mimetypes
import uuid
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from datetime import timedelta, datetime, timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from core.exceptions import DomainError, FileNotFoundError
from custom_account.models import UserModel
from quiz.models import QuizAttempt
from content.models import Course, Enrollment
from media.models import UploadedFile, FileStatus, Component
from media.domains.file_domain import FileDomain
from media.domains.presigned_upload_domain import PresignedUploadDomain



User = get_user_model()

# # django-storages sẽ tự động chặn việc lưu local và đẩy thẳng lên S3 
# # khi lệnh UploadedFile.objects.create chạy.
# @transaction.atomic
# def create_file_upload(user: UserModel, data: dict) -> FileDomain:
#     """
#     Service xử lý nghiệp vụ upload file.
#     Nhận user_id (từ request.user) và data (từ Pydantic Input DTO).
    
#     QUAN TRỌNG: Trả về Model Instance (UploadedFile) 
#     để RoleBasedOutputMixin có thể đọc attributes và @property.
#     """
    
#     # Giải nén dữ liệu từ dict
#     file_data = data.get('file')
#     content_type_str = data.get('content_type_str')
#     object_id = data.get('object_id')
#     component = data.get('component')

#     if not all([file_data, content_type_str, component is not None]):
#         raise DomainError("Dữ liệu input (file, content_type, component) bị thiếu.")
    
#     # Lấy kích thước file (byte)
#     file_size = getattr(file_data, 'size', 0)

#     if file_size > settings.MAX_FILE_SIZE_BYTES:
#         # Đổi ra MB để báo lỗi cho thân thiện
#         size_in_mb = round(file_size / (1024 * 1024), 2)
#         raise DomainError(
#             f"File quá lớn ({size_in_mb}MB). Giới hạn tối đa là {settings.MAX_FILE_SIZE_MB}MB."
#         )

#     if content_type_str and object_id is not None:
#         try:
#             app_label, model_name = content_type_str.split('.')
#             content_type = ContentType.objects.get(app_label=app_label, model=model_name)
#         except (ContentType.DoesNotExist, ValueError, AttributeError):
#             raise DomainError(f"Content_type không hợp lệ: '{content_type_str}'.")

#         try:
#             ParentModel = content_type.model_class()
#             if not ParentModel.objects.filter(pk=object_id).exists():
#                 raise DomainError(f"Không tìm thấy đối tượng '{content_type_str}' với ID {object_id}.")
#         except Exception as e:
#             raise DomainError(f"Lỗi khi kiểm tra đối tượng cha: {e}")
#     else:
#         content_type = None

#     # --- NEW: LOGIC TÍNH MIME TYPE ---
#     # 1. Ưu tiên lấy từ header file mà trình duyệt gửi lên (file_data.content_type)
#     #    Đây là cách nhanh nhất vì file đang nằm trong RAM/Temp
#     mime_type = getattr(file_data, 'content_type', None)

#     # 2. Nếu không có, dùng mimetypes đoán qua tên file (fallback an toàn)
#     if not mime_type:
#         mime_type, _ = mimetypes.guess_type(file_data.name)
    
#     # 3. Nếu vẫn không ra, đặt mặc định
#     if not mime_type:
#         mime_type = 'application/octet-stream'

#     # --- [MỚI] LOGIC LẤY FILE SIZE ---
#     # file_data.size trả về kích thước bằng byte (int)
#     file_size = getattr(file_data, 'size', 0)

#     saved_file_model = UploadedFile.objects.create(
#         file=file_data,
#         original_filename=file_data.name,
#         uploaded_by=user,
#         content_type=content_type,
#         object_id=object_id,
#         component=component,
#         status=FileStatus.STAGING,

#         mime_type=mime_type,
#         file_size=file_size
#     )
    
#     return FileDomain.from_model(saved_file_model)


@transaction.atomic
def initiate_file_upload(user, data: dict) -> dict:
    """
    1. Tạo bản ghi UploadedFile (Status = STAGING)
    2. Sinh ra Presigned URL để Client tự upload lên S3
    """
    original_filename = data.get('filename') # Client gửi tên file lên
    file_type = data.get('file_type')       # Client gửi mime type (video/mp4)
    file_size = data.get('file_size')       # Client gửi size dự kiến
    component = data.get('component')
    
    # 1. Tạo tên file vật lý (key trên S3)
    ext = original_filename.split('.')[-1]
    file_uuid = uuid.uuid4()
    s3_key = f"media/{component}/{datetime.now().year}/{file_uuid}.{ext}"

    # 2. Tạo bản ghi trong DB (Lưu ý: Field 'file' lúc này chưa có file thật)
    # Chúng ta lưu đường dẫn string vào field file.
    instance = UploadedFile.objects.create(
        id=file_uuid,
        uploaded_by=user,
        original_filename=original_filename,
        mime_type=file_type,
        file_size=file_size, # Size dự kiến
        component=component,
        status=FileStatus.STAGING,
        file=s3_key # Django S3 Storage sẽ hiểu đây là path
    )

    # 3. Gọi AWS S3 SDK để tạo Presigned URL
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(signature_version='s3v4')
    )

    # Cấu hình params cho URL
    # ACL='private' để đảm bảo file tải lên không bị public lung tung
    presigned_data = s3_client.generate_presigned_post(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=s3_key,
        Fields={
            'acl': 'private', 
            'Content-Type': file_type
        },
        Conditions=[
            {'acl': 'private'},
            {'Content-Type': file_type},
            ['content-length-range', 0, settings.MAX_FILE_SIZE_BYTES] # Validate size ngay tại S3
        ],
        ExpiresIn=3600 # Link hết hạn sau 1 giờ
    )

    return PresignedUploadDomain(
        file_id=instance.id,
        upload_url=presigned_data['url'],
        upload_fields=presigned_data['fields']
    )


def confirm_file_upload(user, file_id: str) -> FileDomain:
    """
    Xác nhận file đã lên S3 thành công.
    Chuyển trạng thái từ STAGING -> COMMITTED (hoặc READY).
    """
    # 1. Query & Validate Owner
    try:
        file_obj = UploadedFile.objects.get(pk=file_id)
    except UploadedFile.DoesNotExist:
        raise DomainError(f"File {file_id} không tồn tại.")

    if file_obj.uploaded_by != user:
        raise PermissionDenied("Bạn không có quyền xác nhận file này.")

    if file_obj.status == FileStatus.COMMITTED:
        # Nếu đã confirm rồi thì trả về luôn, tránh lỗi
        return FileDomain.from_model(file_obj)

    # 2. CHECK S3 HEAD OBJECT (Cực nhanh - chỉ vài chục ms)
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    try:
        # file_obj.file.name chính là key (path) trên S3
        # Hàm này sẽ throw Exception nếu file không tìm thấy
        response = s3_client.head_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=file_obj.file.name 
        )
        
        # 2.1. Lấy thông tin thực tế từ S3 cập nhật vào DB
        # Đây là bước quan trọng: Client lúc Init có thể khai báo size ảo.
        # Ta lấy size thật từ S3 để lưu DB cho chuẩn.
        real_size = response.get('ContentLength', 0)
        
        if real_size == 0:
             raise DomainError("File trên hệ thống rỗng (0 bytes). Vui lòng upload lại.")
             
        file_obj.file_size = real_size

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == "404":
            raise DomainError("Không tìm thấy file trên hệ thống lưu trữ. Bạn đã upload chưa?")
        else:
            # Lỗi khác (Mạng, Permission...)
            raise DomainError(f"Lỗi kiểm tra file trên S3: {error_code}")

    # 3. Update DB
    file_obj.status = FileStatus.STAGING # Hoặc trạng thái trung gian 'UPLOADED' chờ job quét virus
    file_obj.save(update_fields=['status', 'file_size'])

    return FileDomain.from_model(file_obj)


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


def generate_cloudfront_signed_url(object_key):
    """
    Hàm sinh URL có chữ ký CloudFront.
    Input: object_key (VD: media/lesson/video.mp4)
    Output: https://d2t4....cloudfront.net/media/lesson/video.mp4?Policy=...&Signature=...
    """
    
    # 1. Ghép URL gốc
    base_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{object_key}"
    
    # 2. Thời gian hết hạn (Ví dụ: 1 tiếng)
    expire_date = datetime.now(timezone.utc) + timedelta(hours=1)
    expire_timestamp = int(expire_date.timestamp())

    # 3. Tạo Policy (Luật cho phép truy cập)
    # Luật: Cho phép xem resource này nếu thời gian < expire_timestamp
    policy_dict = {
        "Statement": [{
            "Resource": base_url,
            "Condition": {
                "DateLessThan": {"AWS:EpochTime": expire_timestamp}
            }
        }]
    }
    policy_json = json.dumps(policy_dict, separators=(',', ':'))

    # 4. Đọc Private Key và Ký tên
    try:
        with open(settings.AWS_CLOUDFRONT_KEY_PATH, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
    except FileNotFoundError:
        raise Exception(f"Không tìm thấy private key tại: {settings.AWS_CLOUDFRONT_KEY_PATH}")

    # Ký Policy bằng thuật toán SHA1 (CloudFront yêu cầu)
    signature = private_key.sign(
        policy_json.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA1()
    )

    # 5. Mã hóa Base64 an toàn cho URL (Thay thế ký tự đặc biệt)
    def cloudfront_base64(data):
        return base64.b64encode(data).decode('utf-8').translate(str.maketrans('+=/', '-_~'))

    encoded_policy = cloudfront_base64(policy_json.encode('utf-8'))
    encoded_signature = cloudfront_base64(signature)
    
    # 6. Ghép thành URL cuối cùng
    signed_url = f"{base_url}?Policy={encoded_policy}&Signature={encoded_signature}&Key-Pair-Id={settings.AWS_CLOUDFRONT_KEY_ID}"
    
    return signed_url


def serve_file(request, file_id, user):
    """
    Service trả về URL CloudFront Signed (Tốc độ cao).
    """
    # 1. Lấy object & Check DB
    try:
        file_obj = get_object_or_404(UploadedFile, id=file_id)
    except UploadedFile.DoesNotExist:
        raise FileNotFoundError(f"File {file_id} không tồn tại.")

    # 2. Check quyền (Giữ nguyên logic của bạn)
    if not user_has_access_to_file(user=user, file_object=file_obj):
        return PermissionDenied("Bạn không có quyền truy cập tài nguyên này.")

    if not file_obj.file:
         raise FileNotFoundError("Dữ liệu file bị thiếu trong Database.")

    # 3. SINH URL CLOUDFRONT (Thay thế hoàn toàn đoạn boto3 cũ)
    try:
        # Lấy đường dẫn file (VD: media/2025/abc.mp4)
        s3_key = file_obj.file.name
        
        # Gọi hàm ký tên
        signed_url = generate_cloudfront_signed_url(s3_key)
        print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh", signed_url)
        return signed_url

    except Exception as e:
        print(f"CloudFront Signing Error: {e}")
        # Log lỗi chi tiết để debug
        raise OSError(f"Lỗi khi tạo đường dẫn tải file: {str(e)}")


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