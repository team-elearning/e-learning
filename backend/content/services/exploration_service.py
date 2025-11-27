# import uuid
# from typing import Optional, Any, Dict, List
# from django.db import transaction

# from custom_account.models import UserModel 
# from core.exceptions import DomainError
# from content.models import Exploration, ExplorationState, Category, Tag
# from content.domains.exploration_domain import ExplorationDomain 
# from core.exceptions import ExplorationNotFoundError



# @transaction.atomic
# def create_exploration(owner: UserModel, data: dict) -> ExplorationDomain:
#     """
#     Tạo một exploration mới và state 'init' mặc định.
#     Giống như 'register_user' tạo User và Profile.
#     """
    
#     # 1. Tạo domain object từ dữ liệu DTO
#     # (Giống như user_service tạo UserDomain)
#     exp_domain = ExplorationDomain(
#         id=str(uuid.uuid4()), # Exploration dùng CharField ID
#         title=data["title"],
#         objective=data.get("objective"),
#         language=data.get("language", "vi"),
#         owner_id=owner.id, # Gán owner
#         category_id=data.get("category"), # DTO đã gửi UUID
#         tag_ids=data.get("tags", [])
#     ) 

#     # 2. Chuyển domain sang model để lưu
#     exploration = exp_domain.to_model()
    
#     # Xử lý các trường quan hệ (ForeignKey, ManyToMany)
#     # (user_service không có, nhưng đây là cách làm đúng)
#     if exp_domain.category_id:
#         try:
#             exploration.category = Category.objects.get(pk=exp_domain.category_id)
#         except Category.DoesNotExist:
#             raise DomainError(f"Category {exp_domain.category_id} not found.")

#     # Lưu exploration chính
#     exploration.save()

#     # Xử lý M2M sau khi lưu
#     if exp_domain.tag_ids:
#         try:
#             tags = Tag.objects.filter(pk__in=exp_domain.tag_ids)
#             exploration.tags.set(tags)
#         except Tag.DoesNotExist:
#             raise DomainError("One or more tags not found.")

#     # 3. Tạo aggregate part (giống như tạo Profile)
#     # Tạo một state ban đầu
#     init_state_name = "Introduction" # Tên state mặc định
#     ExplorationState.objects.create(
#         id=f"{exploration.id}:{init_state_name}", # ID của state
#         exploration=exploration,
#         name=init_state_name,
#         content_html="<p>Welcome!</p>",
#         interaction_id="Continue"
#     )
    
#     # Cập nhật exploration với init_state_name
#     exploration.init_state_name = init_state_name
#     exploration.save(update_fields=["init_state_name"])

#     # 4. Trả về Domain object từ Model (giống hệt user_service)
#     return ExplorationDomain.from_model(exploration)


# def update_exploration_metadata(exploration: Exploration, updates: Dict[str, Any]) -> ExplorationDomain:
#     """
#     Cập nhật metadata cho một exploration.
#     Giống hệt 'update_user' (Model -> Domain -> Apply -> Model Save).
#     """
    
#     # 1. Chuyển Model sang Domain
#     domain = ExplorationDomain.from_model(exploration)

#     # 2. Áp dụng updates vào Domain (để validate nếu cần)
#     domain.apply_updates(updates) # Giả định domain có hàm này

#     # 3. Lưu vào database (giống 'update_user')
#     # Tách các trường quan hệ ra xử lý riêng
#     tag_ids = updates.pop('tags', None)
#     category_id = updates.pop('category', None)

#     # Cập nhật các trường đơn giản
#     for key, value in updates.items():
#         if hasattr(exploration, key):
#             setattr(exploration, key, value)
    
#     # Cập nhật FK (Category)
#     if category_id is not None:
#         try:
#             exploration.category = Category.objects.get(pk=category_id)
#         except Category.DoesNotExist:
#             raise DomainError(f"Category {category_id} not found.")
    
#     exploration.save() # Lưu các trường đơn giản và FK

#     # Cập nhật M2M (Tags)
#     if tag_ids is not None:
#         try:
#             tags = Tag.objects.filter(pk__in=tag_ids)
#             exploration.tags.set(tags)
#         except Tag.DoesNotExist:
#             raise DomainError("One or more tags not found.")

#     # 4. Trả về domain object đã cập nhật
#     return ExplorationDomain.from_model(exploration)


# def get_published_explorations() -> List[ExplorationDomain]:
#     """
#     Lấy danh sách các exploration đã published.
#     Giống 'list_all_users_for_admin'.
#     """
#     # Tối ưu: Dùng select/prefetch để tránh N+1 query trong DTO
#     explorations = Exploration.objects.filter(published=True)\
#                                       .select_related('owner', 'category')\
#                                       .prefetch_related('tags')\
#                                       .order_by('-last_updated')
                                      
#     return [ExplorationDomain.from_model(exp) for exp in explorations]


# def get_explorations_for_owner(user: UserModel) -> List[ExplorationDomain]:
#     """ Lấy danh sách exploration (cả draft) cho một owner. """
#     explorations = Exploration.objects.filter(owner=user)\
#                                       .select_related('owner', 'category')\
#                                       .prefetch_related('tags')\
#                                       .order_by('-last_updated')
                                      
#     return [ExplorationDomain.from_model(exp) for exp in explorations]


# def get_full_exploration_details(exploration_id: str, user: Optional[UserModel] = None) -> ExplorationDomain:
#     """
#     Lấy chi tiết một exploration, bao gồm cả states.
#     Giống 'get_user_by_id'.
#     """
#     try:
#         # Tối ưu: Prefetch tất cả dữ liệu lồng ghép
#         exploration = Exploration.objects.select_related('owner', 'category')\
#                                .prefetch_related(
#                                    'tags', 
#                                    'states', 
#                                    'states__media', 
#                                    'states__customization_args'
#                                )\
#                                .get(pk=exploration_id)
#     except Exploration.DoesNotExist:
#         raise ExplorationNotFoundError("Exploration not found.")

#     # Logic nghiệp vụ: Chỉ owner/admin mới được xem bản nháp
#     if not exploration.published:
#         if user is None or (exploration.owner != user and not user.is_staff):
#             raise DomainError("You do not have permission to view this draft.")
    
#     return ExplorationDomain.from_model(exploration) 


# def delete_exploration(exploration: Exploration, user: UserModel):
#     """
#     Xóa một exploration, chứa logic nghiệp vụ.
#     Giống 'delete_user'.
#     """
#     # Logic nghiệp vụ: Không cho phép xóa exploration đã publish
#     if exploration.published and not user.is_staff:
#         raise DomainError("Cannot delete a published exploration. Please unpublish it first.")
    
#     # (user_service của bạn không check, nhưng đây là check quyền sở hữu)
#     if exploration.owner != user and not user.is_staff:
#         raise DomainError("You do not have permission to delete this exploration.")

#     exploration.delete()
#     return True # Trả về True/False giống user_service.deactivate_user


# @transaction.atomic
# def update_full_exploration(exploration: Exploration, full_data: Dict[str, Any], user: UserModel) -> ExplorationDomain:
#     """
#     Cập nhật toàn bộ exploration từ JSON.
#     """
    
#     # 1. Xóa tất cả states cũ (và media/args liên quan)
#     exploration.states.all().delete()
    
#     # 2. Cập nhật metadata của Exploration chính
#     exploration.title = full_data.get('title', exploration.title)
#     exploration.objective = full_data.get('objective', exploration.objective)
#     exploration.language = full_data.get('language', exploration.language)
#     exploration.init_state_name = full_data.get('init_state_name', exploration.init_state_name)
#     # (Thêm các trường metadata khác nếu cần)
    
#     # 3. Tạo lại states từ JSON
#     states_data = full_data.get('states', {})
#     if not states_data:
#         raise DomainError("Exploration must have at least one state.")

#     new_states = []
#     new_media_list = []
#     new_args_list = []

#     for state_name, state_data in states_data.items():
#         new_state = ExplorationState(
#             id=f"{exploration.id}:{state_name}",
#             exploration=exploration,
#             name=state_name,
#             content_html=state_data.get('content', {}).get('html'),
#             interaction_id=state_data.get('interaction', {}).get('id'),
#             card_is_checkpoint=state_data.get('card_is_checkpoint', False)
#         )
#         new_states.append(new_state)

#         # (Bạn có thể thêm logic để parse media và customization args ở đây)
#         # ...
        
#     # 4. Bulk create để tăng tốc
#     ExplorationState.objects.bulk_create(new_states)
    
#     # 5. Lưu exploration chính
#     exploration.save()
    
#     # 6. Lấy lại bản đầy đủ từ DB và trả về domain
#     # (để đảm bảo data nhất quán)
#     updated_exploration = Exploration.objects.get(pk=exploration.id)
#     return ExplorationDomain.from_model(updated_exploration)


# def list_all_explorations() -> List[ExplorationDomain]:
#     """ Lấy TẤT CẢ explorations cho admin (draft, published, mọi owner). """
#     explorations = Exploration.objects.all()\
#                                       .select_related('owner', 'category')\
#                                       .prefetch_related('tags')\
#                                       .order_by('-last_updated')
#     return [ExplorationDomain.from_model(exp) for exp in explorations]