import uuid
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

from custom_account.api.dtos.user_dto import UserPublicOutput, UserAdminOutput
from content.api.dtos.category_dto import CategoryOutput
from content.api.dtos.tag_dto import TagOutput

# ===================================================================
# 1. INPUT DTOs 
# ===================================================================

class ExplorationCreateInput(BaseModel):
    """
    Dùng để nhận dữ liệu đã được validate bởi 'ExplorationCreateSerializer'.
    Giả định serializer đã validate 'category' và 'tags' thành UUIDs.
    """
    title: str = Field(min_length=3)
    objective: Optional[str] = None
    language: str = "vi"
    published: bool = False
    
    category: Optional[uuid.UUID] = None 
    tags: List[uuid.UUID] = []

    def to_dict(self, exclude_none: bool = True) -> dict:
        """ Chuyển model thành dictionary"""
        return self.model_dump(exclude_none=exclude_none)


class UpdateExplorationMetadataInput(BaseModel):
    """
    Dùng để nhận dữ liệu đã được validate bởi 'ExplorationMetadataSerializer'.
    Tất cả các trường đều là Optional.
    """
    title: Optional[str] = Field(None, min_length=3)
    objective: Optional[str] = None
    language: Optional[str] = None
    blurb: Optional[str] = None
    published: Optional[bool] = None
    
    # Trường này chỉ admin/owner mới được cập nhật, 
    # logic phân quyền nên ở service
    author_notes: Optional[str] = None 

    category: Optional[uuid.UUID] = None
    tags: Optional[List[uuid.UUID]] = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        """ Chuyển model thành dictionary """
        return self.model_dump(exclude_none=exclude_none)


# ===================================================================
# 2. OUTPUT DTOs 
# ===================================================================

class ExplorationState(BaseModel):
    """ DTO chi tiết cho ExplorationState lồng ghép """
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    content_text: Optional[str] = None
    interaction_id: Optional[str] = None
    card_is_checkpoint: bool = False
    content_html: Optional[str] = None
    # Bạn có thể thêm các trường khác từ model ExplorationState vào đây


# --- Main Output DTOs ---

class ExplorationPublicOutput(BaseModel):
    """
    Giống như 'UserPublicOutput' của bạn.
    Chỉ chứa các thông tin công khai, không nhạy cảm.
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Thông tin cơ bản
    id: str
    title: str
    blurb: Optional[str] = None
    language: str
    published: bool
    
    # Thông tin quan hệ (công khai)
    owner: Optional[UserPublicOutput] = None
    category: Optional[CategoryOutput] = None
    tags: List[TagOutput] = []
    
    # Thông tin thời gian (công khai)
    last_updated: Optional[datetime] = None
    
    # Dữ liệu nặng (cho view chi tiết)
    # Sẽ là None trong list view (nếu không được prefetch)
    # và được điền trong detail view (nếu được prefetch)
    states: Optional[List[ExplorationState]] = None
    # transitions: Optional[List[Any]] = None # Tùy nếu bạn cần

    def to_dict(self, exclude_none: bool = True) -> dict:
        """ Chuyển model thành dictionary. """
        return self.model_dump(exclude_none=exclude_none)


class ExplorationAdminOutput(BaseModel):
    """
    Giống như 'UserAdminOutput' của bạn.
    Chứa TẤT CẢ thông tin, bao gồm cả các trường nhạy cảm 
    như 'author_notes' và metadata đầy đủ.
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Thông tin cơ bản
    id: str
    title: str
    objective: Optional[str] = None
    language: str
    published: bool
    
    # Metadata đầy đủ
    blurb: Optional[str] = None
    init_state_name: Optional[str] = None
    param_changes: List[Any] = []
    param_specs: Dict[str, Any] = {}
    version: Optional[int] = None
    
    # === TRƯỜNG NHẠY CẢM (chỉ admin/owner thấy) ===
    author_notes: Optional[str] = None 
    
    # Thông tin quan hệ
    owner: Optional[UserAdminOutput] = None
    category: Optional[CategoryOutput] = None
    tags: List[TagOutput] = []
    
    # Thông tin thời gian
    created_on: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    # Dữ liệu nặng (cho view chi tiết)
    states: Optional[List[ExplorationState]] = None
    # transitions: Optional[List[Any]] = None # Tùy nếu bạn cần

    def to_dict(self, exclude_none: bool = True) -> dict:
        """ Chuyển model thành dictionary. """
        return self.model_dump(exclude_none=exclude_none)
    

class ExplorationListOutput(BaseModel):
    """
    CHỈ chứa metadata nhẹ cho LIST VIEW.
    *** Không chứa trường 'states' ***
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    blurb: Optional[str] = None
    language: str
    published: bool
    
    owner: Optional[UserAdminOutput] = None
    category: Optional[CategoryOutput] = None
    tags: List[TagOutput] = []
    
    last_updated: Optional[datetime] = None

    def to_dict(self, exclude_none: bool = True) -> dict:
        return self.model_dump(exclude_none=exclude_none)