import logging
import uuid
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import transaction
from datetime import timedelta
from django.utils import timezone
from django.core.files.storage import default_storage

from core.exceptions import DomainError, UserNotFoundError
from custom_account.models import UserModel
from content.models import Course, Lesson, Enrollment
from media.models import UploadedFile, FileStatus
from media.domains.file_domain import FileDomain



User = get_user_model()

@transaction.atomic
def create_file_upload(user_id: int, data: dict) -> FileDomain:
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

    # Kiểm tra nghiệp vụ 
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise UserNotFoundError(f"User with ID {user_id} not found.")
    
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

    saved_file_model = UploadedFile.objects.create(
        file=file_data,
        original_filename=file_data.name,
        uploaded_by=user,
        content_type=content_type,
        object_id=object_id,
        component=component,
        status=FileStatus.STAGING
    )
    
    return FileDomain.from_model(saved_file_model)


@transaction.atomic
def commit_files_for_object(file_paths: list[str], related_object) -> int:
    """
    Tìm các file 'staging' bằng đường dẫn (path) và "commit" chúng,
    gán chúng vào một đối tượng (Course, Lesson, v.v.).
    
    Hàm này được gọi bởi các service khác (ví dụ: create_course).
    """
    logger.info(f"Bắt đầu commit file cho đối tượng {related_object}...")
    
    if not file_paths:
        logger.warning("Không có file path nào được cung cấp để commit.")
        return 0

    # 1. Tìm ContentType của đối tượng (Course, Lesson, etc.)
    try:
        content_type = ContentType.objects.get_for_model(related_object)
        object_id = related_object.pk
    except Exception as e:
        logger.error(f"Lỗi khi lấy ContentType cho {related_object}: {e}", exc_info=True)
        # Ném lỗi để transaction bên ngoài (create_course) có thể ROLLBACK
        raise DomainError(f"Không thể lấy ContentType cho {related_object}")

    # 2. Tìm các bản ghi UploadedFile khớp với các đường dẫn
    #    Chúng ta giả định file_paths là các đường dẫn chính xác
    #    được lưu trong trường `file` của model UploadedFile.
    files_to_commit = UploadedFile.objects.filter(
        file__in=file_paths,
        status=FileStatus.STAGING
    )
    
    count = files_to_commit.count()
    if count == 0:
        # Điều này có thể xảy ra nếu file không tồn tại hoặc đã được commit
        logger.warning(f"Không tìm thấy file STAGING nào khớp với: {file_paths}")
        return 0

    # 3. Cập nhật (commit) tất cả các file tìm thấy
    files_to_commit.update(
        status=FileStatus.COMMITTED,
        content_type=content_type,
        object_id=object_id,
        expires_at=None  # Xóa ngày hết hạn (nếu có)
    )
    
    logger.info(f"Đã commit thành công {count} file cho {content_type}:{object_id}.")
    
    return count


@transaction.atomic
def commit_files_by_ids_for_object(file_ids: list[str], related_object) -> int:
    logger.info(f"Bắt đầu commit file (bằng ID) cho đối tượng {related_object}...")

    if not file_ids:
        logger.warning("Không có ID file nào được cung cấp để commit.")
        return 0

    # 1. Chuẩn hóa danh sách ID đầu vào thành Set (để loại trùng và so sánh)
    # Chuyển tất cả về string để đảm bảo so sánh đúng với UUID từ DB
    target_ids = set(str(fid) for fid in file_ids)

    # 2. Lấy ContentType (Giữ nguyên)
    try:
        content_type = ContentType.objects.get_for_model(related_object)
        object_id = str(related_object.pk)
    except Exception as e:
        logger.error(f"Lỗi khi lấy ContentType: {e}", exc_info=True)
        raise DomainError(f"Không thể lấy ContentType cho {related_object}")

    # 3. Truy vấn DB
    # Lưu ý: Chưa update ngay, mà lấy danh sách ID tồn tại trước
    files_qs = UploadedFile.objects.filter(id__in=target_ids)
    
    # Lấy ra danh sách các ID thực sự tìm thấy trong DB
    # values_list trả về UUID object, nên cần ép kiểu str để so sánh với target_ids
    found_ids = set(str(uid) for uid in files_qs.values_list('id', flat=True))

    # 4. --- TÌM RA ID BỊ THIẾU ---
    # Phép trừ tập hợp: Có trong target_ids nhưng không có trong found_ids
    missing_ids = target_ids - found_ids

    if missing_ids:
        error_msg = f"Không tìm thấy file với các ID sau: {missing_ids}"
        logger.error(error_msg)
        # Bắn lỗi ngay lập tức, transaction sẽ rollback
        raise DomainError(error_msg)

    # 5. Nếu không thiếu gì, tiến hành Update
    updated_count = files_qs.update(
        status=FileStatus.COMMITTED,
        content_type=content_type,
        object_id=object_id,
    )

    logger.info(f"Đã commit thành công {updated_count} file cho {content_type}:{object_id}.")
    
    return updated_count


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
    Xóa một file (cả bản ghi CSDL và file vật lý).
    """
    logger.info(f"Service: Xóa file ID {file_id}...")
    
    file_model = get_file_model(file_id)
    
    # 1. Xóa file vật lý khỏi S3/media
    # (Nếu không có file vật lý, nó sẽ bỏ qua một cách an toàn)
    file_model.file.delete(save=False)
    
    # 2. Xóa bản ghi (record) khỏi CSDL
    file_model.delete()
    
    logger.info(f"Service: Đã xóa thành công file ID {file_id}.")
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