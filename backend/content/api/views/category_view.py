# from typing import Any, Dict
# from rest_framework import status, permissions
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from django.core.exceptions import ValidationError

# from core.api.mixins import RoleBasedOutputMixin
# from content.serializers import CategorySerializer
# from content.api.dtos.category_dto import CategoryInput, UpdateCategoryInput, CategoryOutput
# from content.domains.category_domain import CategoryDomain
# from content.services import category_service
# from core.exceptions import DomainError
# import logging

# logger = logging.getLogger(__name__)


# class PublicCategoryListView(APIView):
#     """
#     GET /api/categories/   (public) - list all categories
#     """
#     permission_classes = [permissions.AllowAny]
#     output_dto_public = CategoryOutput

#     def get(self, request):
#         try:
#             category_domains = category_service.list_all_categories()  # List[CategoryDomain]
#             return Response({"instance": category_domains}, status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.error("Failed to list categories: %s", e, exc_info=True)
#             return Response({"detail": "Failed to load categories."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class PublicCategoryDetailView(APIView):
#     """
#     GET /api/categories/{id}/  (public) - view category detail
#     """
#     permission_classes = [permissions.AllowAny]
#     output_dto_public = CategoryOutput

#     def get(self, request, id):
#         try:
#             category_domain = category_service.get_category_by_id(id)
#             return Response({"instance": category_domain}, status=status.HTTP_200_OK)
#         except DomainError:
#             return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error("Failed to fetch category %s: %s", id, e, exc_info=True)
#             return Response({"detail": "Failed to fetch category."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# class AdminCategoryListView(APIView):
#     """
#     POST /api/admin/categories/  (admin) - create category
#     NOTE: register this view under an admin-prefixed URL (e.g., /api/admin/categories/)
#     """
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
#     output_dto_admin = CategoryOutput

#     def post(self, request):
#         serializer = CategorySerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
#         except Exception:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             input_dto = CategoryInput(**validated_data)
#         except Exception as e:
#             return Response({"detail": f"Invalid input data: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             new_category_domain = category_service.create_category(input_dto.model_dump() if hasattr(input_dto, "model_dump") else input_dto.__dict__)
#             return Response({"instance": new_category_domain}, status=status.HTTP_201_CREATED)
#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error("Unexpected error creating category: %s", e, exc_info=True)
#             return Response({"detail": "Unexpected error occurred while creating category."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def get(self, request):
#         """
#         List all categories (admin only)
#         """
#         try:
#             # Service returns a list of DOMAIN ENTITIES
#             category_domains: list[CategoryDomain] = self.category_service.list_all_categories()
#             return Response({"instance": category_domains}, status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.error("Unexpected error listing categories: %s", e, exc_info=True)
#             return Response(
#                 {"detail": f"An unexpected error occurred: {str(e)}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class AdminCategoryDetailView(APIView):
#     """
#     GET    /api/admin/categories/{id}/  (admin) - view category
#     PUT/PATCH /api/admin/categories/{id}/  (admin) - update
#     DELETE  /api/admin/categories/{id}/      (admin) - delete
#     """
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
#     output_dto_admin = CategoryOutput

#     def get(self, request, id):
#         try:
#             category_domain = category_service.get_category_by_id(category_id=id)
#             return Response({"instance": category_domain}, status=status.HTTP_200_OK)
#         except DomainError:
#             return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error("Unexpected error fetching category %s: %s", id, e, exc_info=True)
#             return Response({"detail": "Unexpected error while fetching category."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def patch(self, request, id):
#         serializer = CategorySerializer(data=request.data, partial=True)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
#         except Exception:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             update_dto = UpdateCategoryInput(**validated_data)
#         except Exception as e:
#             return Response({"detail": f"Invalid update payload: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#         updates_payload: Dict[str, Any] = update_dto.model_dump(exclude_none=True) if hasattr(update_dto, "model_dump") else {k: v for k, v in update_dto.__dict__.items() if v is not None}
#         if not updates_payload:
#             return Response({"detail": "No fields to update."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             updated_domain = category_service.update_category(category_id=id, updates=updates_payload)
#             return Response({"instance": updated_domain}, status=status.HTTP_200_OK)
#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error("Unexpected error updating category %s: %s", id, e, exc_info=True)
#             return Response({"detail": "Unexpected error during update."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def delete(self, request, id):
#         try:
#             category_service.delete_category(category_id=id)
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error("Unexpected error deleting category %s: %s", id, e, exc_info=True)
#             return Response({"detail": "Unexpected error during deletion."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



