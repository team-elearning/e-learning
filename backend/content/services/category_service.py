# from typing import Any, Dict, List, Optional
# from django.core.exceptions import ObjectDoesNotExist, ValidationError
# from django.db import transaction

# from content.models import Category
# from content.domains.category_domain import CategoryDomain
# from core.exceptions import DomainError


# def create_category(data: Dict[str, Any]) -> CategoryDomain:
#     """
#     Service to create a new Category aggregate.
#     Enforces domain invariants (e.g., unique name/slug).
#     """

#     # Business rule: unique name & slug
#     if Category.objects.filter(name=data["name"]).exists():
#         raise DomainError("Category name already exists.")
#     if Category.objects.filter(slug=data["slug"]).exists():
#         raise DomainError("Category slug already exists.")

#     # Create domain object
#     domain = CategoryDomain(name=data["name"], slug=data["slug"])

#     # Convert domain -> model and save
#     model = domain.to_model()
#     model.save()

#     return CategoryDomain.from_model(model)


# def list_all_categories() -> List[CategoryDomain]:
#     """
#     Returns all CategoryDomain objects in the system.
#     """
#     models = Category.objects.all().order_by("name")
#     return [CategoryDomain.from_model(m) for m in models]


# def get_category_by_id(category_id: str) -> CategoryDomain:
#     """
#     Fetch a category by its UUID.
#     """
#     try:
#         model = Category.objects.get(id=category_id)
#         return CategoryDomain.from_model(model)
#     except ObjectDoesNotExist:
#         raise DomainError("Category not found.")


# def update_category(category_id: str, updates: Dict[str, Any]) -> CategoryDomain:
#     """
#     Updates category fields through domain logic.
#     """
#     try:
#         model = Category.objects.get(id=category_id)
#     except Category.DoesNotExist:
#         raise DomainError("Category not found.")

#     # Convert model → domain
#     domain = CategoryDomain.from_model(model)

#     # Áp dụng các thay đổi qua domain
#     domain.apply_updates(updates)

#     # Cập nhật model
#     for k, v in updates.items():
#         if hasattr(model, k):
#             setattr(model, k, v)
#     model.save()

#     return CategoryDomain.from_model(model)


# def delete_category(category_id: str) -> bool:
#     """
#     Deletes a category, enforcing domain-level constraints if needed.
#     """
#     try:
#         model = Category.objects.get(id=category_id)
#     except Category.DoesNotExist:
#         raise DomainError("Category not found.")

#     # (Optional) enforce domain rule — e.g., cannot delete category if has products
#     domain = CategoryDomain.from_model(model)
#     if not domain.can_be_deleted():
#         raise DomainError("Cannot delete this category (it may contain products).")

#     model.delete()
#     return True


# @transaction.atomic
# def synchronize_slugs() -> dict:
#     """
#     Fix missing or duplicate slugs.
#     """
#     fixed_count = 0
#     seen = set()

#     for cat in Category.objects.all():
#         if not cat.slug or cat.slug in seen:
#             cat.slug = f"{cat.name.lower().replace(' ', '-')}-{cat.id.hex[:6]}"
#             cat.save(update_fields=["slug"])
#             fixed_count += 1
#         seen.add(cat.slug)

#     return {
#         "categories_fixed": fixed_count,
#         "detail": "Slug synchronization complete."
#     }


