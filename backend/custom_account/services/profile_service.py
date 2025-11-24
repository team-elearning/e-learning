import logging
from typing import List
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from core.exceptions import ProfileNotFoundError
from custom_account.domains.profile_domain import ProfileDomain
from custom_account.models import Profile , UserModel
from media.models import UploadedFile, FileStatus, Component
from core.exceptions import DomainError



logger = logging.getLogger(__name__)
def create_default_profile(user_id: int):
    """
    Service-layer method to create a default profile for a user.
    Contains business logic for *if* a profile can be created.
    """
    # Fetch the user from the repository
    try:
        user_to_link = UserModel.objects.get(id=user_id)
    except UserModel.DoesNotExist:
        raise ValidationError("User not found.")

    # Check if a profile already exists for this user
    if Profile.objects.filter(user=user_to_link).exists():
        raise ValidationError("Profile already exists for this user.")
        
    # Create the default object (repository operation)
    try:
        new_profile = Profile.objects.create(user=user_to_link)
        return new_profile
    except Exception as e:
        logger.error(f"Error creating default profile in service: {e}", exc_info=True)
        raise ValidationError(f"Could not create profile: {e}")


def create_profile(domain: ProfileDomain) -> ProfileDomain:
    profile = Profile.objects.create(
        user_id=domain.user_id,
        display_name=domain.display_name,
        avatar_url=domain.avatar_url,
        dob=domain.dob,
        gender=domain.gender,
        language=domain.language,
        metadata=domain.metadata,
    )
    return ProfileDomain.from_model(profile)


def _delete_old_avatar(old_file_id: str):
    """Helper để xóa file cũ, tránh rác ổ cứng"""
    try:
        old_file = UploadedFile.objects.get(id=old_file_id)
        # Xóa file vật lý
        old_file.file.delete(save=False)
        # Xóa bản ghi DB
        old_file.delete()
    except UploadedFile.DoesNotExist:
        pass



@transaction.atomic
def update_profile(user_id: int, updates: dict) -> ProfileDomain:
    profile = Profile.objects.select_related('user').get(user_id=user_id)
    user = profile.user

    # --- XỬ LÝ USER MODEL ---
    # Tách các field của User ra khỏi dict updates
    user_fields = ['username', 'email', 'phone']
    user_has_changed = False

    for field in user_fields:
        if field in updates:
            value = updates.pop(field) # Lấy ra và xóa khỏi dict updates (để phần dưới chỉ còn field của Profile)
            
            # Chỉ update nếu giá trị khác hiện tại
            if getattr(user, field) != value:
                setattr(user, field, value)
                user_has_changed = True

    if user_has_changed:
        # Check unique lần cuối (Service layer safeguard)
        # Logic này có thể thừa nếu Serializer đã bắt, nhưng an toàn cho Domain
        if UserModel.objects.filter(username=user.username).exclude(pk=user.pk).exists():
             raise DomainError("Username đã tồn tại.")
        
        user.save()

    # --- XỬ LÝ PROFILE MODEL ---

    # 1. Tách avatar_id ra xử lý riêng
    new_avatar_id = updates.pop('avatar_id', None)
    
    # 2. Cập nhật các field thông thường (Text)
    for field, value in updates.items():
        if hasattr(profile, field):
            setattr(profile, field, value)
            
    # 3. Logic xử lý Avatar (Claiming Logic)
    if new_avatar_id:
        # Case A: User muốn xóa avatar (gửi chuỗi rỗng hoặc null đặc biệt nếu cần)
        # Ở đây giả sử gửi UUID tức là muốn đổi avatar mới
        
        # Tìm file trong bảng UploadedFile
        try:
            # Chỉ lấy file STAGING do chính user này up lên
            # (Security check: Tránh user A lấy UUID file của user B)
            new_avatar_file = UploadedFile.objects.get(
                id=new_avatar_id, 
                uploaded_by_id=user_id,
                status=FileStatus.STAGING 
            )
            
            # a. Đánh dấu file cũ là rác (để Cron job xóa sau) 
            # hoặc xóa luôn nếu file lưu local
            if profile.avatar_id:
                 _delete_old_avatar(profile.avatar_id)

            # b. Commit file mới
            new_avatar_file.status = FileStatus.COMMITTED
            new_avatar_file.component = Component.USER_AVATAR # Gán đúng component
            new_avatar_file.content_type = ContentType.objects.get_for_model(Profile)
            new_avatar_file.object_id = str(profile.pk) # Link ngược về Profile
            new_avatar_file.save()

            # c. Lưu vào Profile
            profile.avatar_id = str(new_avatar_file.id) # Lưu ID hoặc URL tùy bạn

        except UploadedFile.DoesNotExist:
            raise DomainError("File ảnh không hợp lệ hoặc phiên upload đã hết hạn.")

    profile.save()
    return ProfileDomain.from_model(profile)


def get_profile_by_user(user_id: int) -> ProfileDomain:
    try:
        # select_related('user') giúp join bảng User ngay trong 1 câu query
        profile = Profile.objects.select_related('user').get(user_id=user_id)
        return ProfileDomain.from_model(profile)
    except Profile.DoesNotExist:
        # Nếu chưa có profile, có thể ném lỗi hoặc tạo profile rỗng tùy logic
        raise ProfileNotFoundError("Ko tìm thấy profile")


def list_all_profiles() -> List[ProfileDomain]:
    """
    Gets all profiles as a list of ProfileDomain entities.

    This follows the service layer pattern where the service
    interacts with the Model but returns Domain Entities.
    """
    profile_models = Profile.objects.select_related("user").all().order_by('user_id')
    
    # Convert models to domain entities.
    profile_domains = [ProfileDomain.from_model(profile) for profile in profile_models]
    
    # Return the list of domain entities
    return profile_domains


def delete_profile(user_id: int):
    """
    Service-layer method to delete a profile.
    Contains business logic for *if* a profile can be deleted.
    """
    # Fetch the domain object from the repository
    try:
        profile_to_delete = Profile.objects.get(user_id=user_id)
    except Profile.DoesNotExist:
        # Service layer should raise a domain/validation error, not Http404
        raise ValidationError("Profile not found.")
    
    profile_to_delete.delete()