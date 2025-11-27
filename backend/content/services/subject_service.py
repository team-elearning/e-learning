# taxonomy/services/subject_service.py
import logging
from typing import Any, Dict, List
from uuid import UUID
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from django.utils.text import slugify

from content.models import Subject
from content.domains.subject_domain import SubjectDomain
from core.exceptions import DomainError, SubjectNotFoundError, DomainValidationError



logger = logging.getLogger(__name__)
# --- Helper Function ---

# def _get_subject_model(subject_id: UUID) -> Subject:
#     """
#     Hàm helper để lấy một Subject model hoặc raise SubjectNotFoundError.
#     """
#     try:
#         return Subject.objects.get(pk=subject_id)
#     except ObjectDoesNotExist:
#         raise SubjectNotFoundError("Không tìm thấy chủ đề (Subject).")

# --- Service Functions ---

@transaction.atomic
def create_subject(data: Dict[str, Any]) -> SubjectDomain:
    """
    Tạo một chủ đề (subject) mới.
    
    Hàm này tuân theo logic của `register_user`:
    1. Kiểm tra logic nghiệp vụ (tính duy nhất).
    2. Tạo SubjectDomain.
    3. Chuyển Domain -> Model và lưu.
    4. Trả về SubjectDomain từ model đã lưu.
    """
    
    title = data.get('title')
    slug = data.get('slug')

    if not title:
        raise DomainError("Tiêu đề (title) là bắt buộc.")
    
    if Subject.objects.filter(title=title).exists():
        raise DomainError(f"Tiêu đề '{title}' đã tồn tại.")

    # 1. Tạo slug nếu không được cung cấp
    if not slug:
        slug = slugify(title)
        data['slug'] = slug # Cập nhật lại data dict
    
    # 2. Thực thi các bất biến nghiệp vụ (tính duy nhất)
    if Subject.objects.filter(slug=slug).exists():
        raise DomainError(f"Slug '{slug}' đã tồn tại.")

    # 3. Tạo Domain 
    try:
        subject_domain = SubjectDomain(title=title, slug=slug)
        
        # 4. Chuyển đổi sang Model và lưu
        subject_model = subject_domain.to_model()
        subject_model.save()

        # 5. Trả về domain từ model đã lưu (để có ID)
        return SubjectDomain.from_model(subject_model)
    
    except IntegrityError as e:
        # Bắt các lỗi database (như unique constraint) mà có thể bị lọt
        logger.warning(f"Lỗi khi tạo Subject: {e}")
        raise DomainError(f"Không thể tạo chủ đề: {e}")
    except Exception as e:
        raise DomainError(f"Lỗi không xác định khi tạo chủ đề: {e}")


# @transaction.atomic
# def update_subject(subject_id: UUID, updates: Dict[str, Any]) -> SubjectDomain:
#     """
#     Cập nhật chủ đề từ một dictionary các cập nhật.
    
#     Hàm này tuân theo logic của `update_user`:
#     1. Lấy model.
#     2. Chuyển sang Domain.
#     3. Kiểm tra logic nghiệp vụ (tính duy nhất của các trường update).
#     4. Áp dụng updates vào Domain (giả định có `apply_updates`).
#     5. Áp dụng updates vào Model và lưu.
#     6. Trả về Domain đã cập nhật.
#     """
    
#     subject_model = _get_subject_model(subject_id)
#     domain = SubjectDomain.from_model(subject_model)

#     # 1. Validate tính duy nhất (Bất biến)
#     new_slug = updates.get('slug')
#     new_title = updates.get('title')

#     if new_slug and new_slug != domain.slug:
#         if Subject.objects.filter(slug=new_slug).exclude(pk=subject_id).exists():
#             raise DomainError(f"Slug '{new_slug}' đã tồn tại.")
    
#     if new_title and new_title != domain.title:
#         if Subject.objects.filter(title=new_title).exclude(pk=subject_id).exists():
#             raise DomainError(f"Tiêu đề '{new_title}' đã tồn tại.")
        
#         # Nếu title thay đổi VÀ slug không được cung cấp, tự động cập nhật slug
#         if not new_slug:
#             new_slug = slugify(new_title)
#             if Subject.objects.filter(slug=new_slug).exclude(pk=subject_id).exists():
#                     raise DomainError(f"Slug '{new_slug}' (tự tạo) đã tồn tại.")
#             updates['slug'] = new_slug # Thêm vào dict để được lưu

#     # 2. Áp dụng updates vào domain (giống `update_user`)
#     # (Giả định SubjectDomain có phương thức này)
#     domain.apply_updates(updates) 

#     # 3. Lưu vào database (giống `update_user`)
#     try:
#         for key, value in updates.items():
#             if hasattr(subject_model, key):
#                 setattr(subject_model, key, value)
        
#         subject_model.full_clean() # Validate model-level constraints
#         subject_model.save()
        
#         return domain # Trả về domain đã update (giống `update_user`)
    
#     except DomainValidationError as e:
#         raise DomainError(f"Dữ liệu không hợp lệ: {e}")
#     except Exception as e:
#         raise DomainError(f"Lỗi khi cập nhật chủ đề: {e}")


# def delete_subject(subject_id: UUID) -> bool:
#     """
#     Xóa vĩnh viễn một chủ đề.
#     """
#     subject_model = _get_subject_model(subject_id)
    
#     try:
#         subject_model.delete()
#         return True
#     except IntegrityError as e:
#         # Bắt lỗi nếu Subject đang được sử dụng (ví dụ: ProtectedError)
#         raise DomainError(f"Không thể xóa chủ đề: Chủ đề đang được sử dụng. Lỗi: {e}")
#     except Exception as e:
#         raise DomainError(f"Lỗi không xác định khi xóa chủ đề: {e}")


# def get_subject_by_id(subject_id: UUID) -> SubjectDomain:
#     """
#     Lấy một chủ đề (SubjectDomain) bằng ID của nó.
#     """
#     subject_model = _get_subject_model(subject_id) # Đã bao gồm try/except
#     return SubjectDomain.from_model(subject_model)


def list_all_subjects() -> List[SubjectDomain]:
    """
    Lấy tất cả các chủ đề (SubjectDomain), sắp xếp theo tiêu đề.
    
    Hàm này tuân theo logic của `list_all_users_for_admin`:
    1. Lấy tất cả Model.
    2. Chuyển đổi List[Model] -> List[Domain].
    3. Trả về List[Domain].
    """
    try:
        subject_models = Subject.objects.all().order_by('title')
        subject_domains = [SubjectDomain.from_model(s) for s in subject_models]
        return subject_domains
    except Exception as e:
        # Ghi log lỗi ở đây
        raise DomainError(f"Lỗi khi lấy danh sách chủ đề: {e}")