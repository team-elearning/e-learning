import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import logging
import uuid
import threading
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
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
from media.domains.presigned_upload_domain import PresignedUploadDomain
from media.domains.cleanup_task_domain import CleanupTaskDomain
from media.services.cloud_service import generate_cloudfront_signed_url



User = get_user_model()

logger = logging.getLogger(__name__)

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

    PUBLIC_COMPONENTS = ['course_thumbnail', 'user_avatar', 'site_logo']
    
    if component in PUBLIC_COMPONENTS:
        acl_policy = 'public-read'  # File này ai cũng đọc được
    else:
        acl_policy = 'private'      # File này phải chính chủ mới đọc được

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
            'acl': acl_policy, 
            'Content-Type': file_type
        },
        Conditions=[
            {'acl': acl_policy},
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
    
    print(f"DEBUG STORAGE: {file_obj.file.storage}")

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


CLEANUP_LOCK_ID = "cleanup_task_running_lock"
def trigger_background_cleanup(days_old: int = 1) -> CleanupTaskDomain:
    """
    Kích hoạt tiến trình dọn dẹp chạy ngầm (Threading).
    Trả về CleanupTaskDomain báo trạng thái (Thành công hoặc Bị khóa).
    """
    
    # 1. Check Lock
    if cache.get(CLEANUP_LOCK_ID):
        return CleanupTaskDomain.locked(
            message="Tiến trình dọn dẹp ĐANG CHẠY. Vui lòng đợi nó hoàn tất."
        )

    # 2. Định nghĩa hàm Worker (Chạy trong Thread)
    def _run_worker():
        try:
            # Set Lock (Hết hạn sau 10 phút)
            cache.set(CLEANUP_LOCK_ID, "running", timeout=600)
            print(f">>> [Service] Thread Start: Dọn file cũ hơn {days_old} ngày...")
            
            # TRUYỀN THAM SỐ VÀO ĐÂY
            # days: xóa file staging cũ
            # clean_broken: True để bật chế độ quét file lỗi (nếu muốn admin chạy cái này)
            call_command('cleanup_files', days=days_old)
            
            print(">>> [Service] Thread Done: Hoàn tất.")
        except Exception as e:
            print(f">>> [Service] Thread Error: {e}")
        finally:
            # Luôn giải phóng lock
            cache.delete(CLEANUP_LOCK_ID)

    # 3. Khởi chạy Thread
    task_thread = threading.Thread(target=_run_worker, daemon=True)
    task_thread.start()

    return CleanupTaskDomain.started(
        message="Đã kích hoạt tiến trình dọn dẹp ngầm thành công.",
        lock_id=CLEANUP_LOCK_ID
    )


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
    Service xóa file (Xóa cả DB và File vật lý trên S3).
    """
    logger.info(f"Service: Yêu cầu xóa file ID {file_id}...")
    
    # 1. Tìm file trong DB
    try:
        file_obj = UploadedFile.objects.get(pk=file_id)
    except UploadedFile.DoesNotExist:
        return None

    # 2. Xóa file vật lý trên AWS S3
    # Mặc dù CloudFront còn cache, nhưng xóa gốc S3 là quan trọng nhất để tiết kiệm tiền.
    if file_obj.file and file_obj.file.name:
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )
            
            s3_client.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_obj.file.name
            )
            logger.info(f"AWS S3: Đã xóa object {file_obj.file.name}")
            
        except Exception as e:
            # Chỉ log warning, không chặn việc xóa DB (để tránh lỗi logic)
            logger.warning(f"Không thể xóa file trên S3: {str(e)}")

    # 3. Xóa bản ghi trong DB
    file_obj.delete()
    
    logger.info(f"Service: Đã xóa bản ghi DB ID {file_id}.")
    return None


def _check_quiz_access(user, quiz_obj):
        """
        Kiểm tra user có đủ điều kiện làm bài Quiz không.
        Check: Thời gian mở/đóng, Số lần làm bài (Attempts).
        Không check Enrollment ở đây (Enrollment check ở tầng Course rồi).
        """
        # 1. Admin/Giảng viên sở hữu -> Luôn OK (để họ còn test bài)
        if user.is_staff or user.is_superuser:
            return True
        if quiz_obj.owner == user:
            return True

        now = timezone.now()

        # 2. Check thời gian Mở (Time Open)
        if quiz_obj.time_open and now < quiz_obj.time_open:
            # Chưa đến giờ mở
            return False

        # 3. Check thời gian Đóng (Deadline)
        if quiz_obj.time_close and now > quiz_obj.time_close:
            # Đã hết hạn
            # Tùy nghiệp vụ: Nếu hết hạn nhưng user muốn xem lại bài đã làm thì OK.
            # Nhưng nếu muốn "Start" bài mới thì False. 
            # Ở đây ta chặn access nói chung để bảo mật đề thi.
            return False

        # 4. Check chế độ Ôn luyện (Practice)
        # Nếu là practice thì thường cho làm thoải mái, bỏ qua check số lần
        if quiz_obj.mode == 'practice':
            return True

        # 5. Check số lần làm bài (Max Attempts) cho chế độ Exam
        if quiz_obj.max_attempts is not None:
            # Đếm số lần user đã làm (QuizAttempt)
            # Giả sử bạn có model QuizAttempt
            attempt_count = QuizAttempt.objects.filter(
                user=user, 
                quiz=quiz_obj
            ).count()
            
            if attempt_count >= quiz_obj.max_attempts:
                return False # Hết lượt làm bài

        return True


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
        raise PermissionDenied("Bạn không có quyền truy cập tài nguyên này.")

    if not file_obj.file:
         raise FileNotFoundError("Dữ liệu file bị thiếu trong Database.")

    # CHIẾN THUẬT QUẢN LÝ THỜI GIAN
    expire_minutes = 60 # Mặc định 1 tiếng cho file thường (PDF, Docx)

    # 1. Nếu là Video: Cho sống lâu (đề phòng user pause đi ăn cơm)
    # Tốt nhất là 6 tiếng hoặc 12 tiếng. CloudFront không tính phí dựa trên thời gian hết hạn.
    # Đừng keo kiệt chỗ này, UX quan trọng hơn.
    if file_obj.mime_type and file_obj.mime_type.startswith('video/'):
        expire_minutes = 360 # 6 tiếng
    
    # 2. Nếu là Ảnh (Avatar/Thumbnail): Cho sống rất lâu để Browser Cache hiệu quả
    elif file_obj.mime_type and file_obj.mime_type.startswith('image/'):
        expire_minutes = 1440 # 24 tiếng (1 ngày)

    # 3. Nếu là file download nặng (trên 100MB): Tăng thêm thời gian đề phòng mạng chậm
    elif file_obj.file_size > 100 * 1024 * 1024: # > 100MB
        expire_minutes = 120 # 2 tiếng

    # 3. SINH URL CLOUDFRONT (Thay thế hoàn toàn đoạn boto3 cũ)
    try:
        # Lấy đường dẫn file (VD: media/2025/abc.mp4)
        s3_key = file_obj.file.name
        
        # Gọi hàm ký tên
        signed_url = generate_cloudfront_signed_url(s3_key, expire_minutes=expire_minutes)
        print("hhhhhhhhhhhhhhhhhhhhhhhhh", signed_url)
        return signed_url

    except Exception as e:
        print(f"CloudFront Signing Error: {e}")
        # Log lỗi chi tiết để debug
        raise OSError(f"Lỗi khi tạo đường dẫn tải file: {str(e)}")


# def _get_best_mime_type(file_obj):
#     """
#     Hàm ưu tiên lấy từ DB, nếu không có thì đoán.
#     """
#     # Ưu tiên 1: Lấy từ DB (Nhanh nhất - O(1))
#     # Vì bạn mới thêm trường này, nên các file cũ có thể là Null/None
#     if file_obj.mime_type:
#         return str(file_obj.mime_type)

#     # Ưu tiên 2: Đoán từ tên file gốc (Nhanh nhì)
#     # VD: 'bai_giang.mp4' -> 'video/mp4'
#     guessed_type, _ = mimetypes.guess_type(file_obj.original_filename or file_obj.file.name)
#     if guessed_type:
#         return guessed_type

#     # Ưu tiên 3: Mặc định an toàn (Binary)
#     return 'application/octet-stream'

# def _is_browser_viewable(mime_type):
#     """
#     Danh sách các loại file trình duyệt có thể mở được ngay
#     """
#     if not mime_type: return False
    
#     viewable_types = [
#         'application/pdf',
#         'video/mp4', 'video/webm', 'video/ogg',
#         'audio/mpeg', 'audio/ogg', 'audio/wav',
#         'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
#         'text/plain'
#     ]
#     return mime_type in viewable_types


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