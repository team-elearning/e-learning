import logging
import uuid
from django.http import Http404
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from content.models import ContentBlock, Lesson
from content.services import content_block_service
from content.serializers import ConvertBlockSerializer, ContentBlockCreateSerializer, ContentBlockUpdateSerializer, ContentBlockReorderSerializer
from content.api.dtos.content_block_dto import ContentBlockInput, ContentBlockUpdateInput, ContentBlockAdminOutput, ContentBlockPublicOutput
from content.domains.content_block_domain import ContentBlockDomain
from core.exceptions import DomainError 
from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin
from core.api.permissions import IsInstructor, IsCourseOwner



# logger = logging.getLogger(__name__)

# class PublicLessonBlockListView(RoleBasedOutputMixin, APIView):
#     """
#     GET lesson-versions/<uuid:lesson_version_id>/blocks/
    
#     API công khai cho HỌC SINH (player) đã ghi danh.
#     """
#     permission_classes = [permissions.IsAuthenticated]
    
#     output_dto_public = ContentBlockPublicOutput
#     output_dto_admin = ContentBlockAdminOutput 

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.service = content_block_service

#     def get(self, request, lesson_version_id):
#         """
#         Ủy quyền toàn bộ logic nghiệp vụ cho service.
#         """
#         try:
#             block_domains = self.service.get_public_blocks_for_version(
#                 user=request.user,
#                 lesson_version_id=lesson_version_id
#             )
            
#             # Trả về list domain, Mixin sẽ lo phần serialize
#             return Response({"instance": block_domains}, status=status.HTTP_200_OK)

#         # Bắt các lỗi nghiệp vụ cụ thể từ service
#         except exceptions.LessonVersionNotFoundError:
#             return Response({"detail": "Không tìm thấy bài học."}, status=404)
        
#         except exceptions.VersionNotPublishedError:
#             return Response({"detail": "Nội dung bài học chưa được xuất bản."}, status=404)

#         except exceptions.NotEnrolledError:
#             return Response({"detail": "Bạn chưa ghi danh vào khóa học."}, status=403)
            
#         except Exception as e:
#             logger.error(f"Lỗi public Lấy block: {e}", exc_info=True)
#             return Response({"detail": "Lỗi hệ thống."}, status=500)


# #=================================================================
# # API: admin/lesson-versions/<uuid:lesson_version_id>/blocks/
# #=================================================================
# class AdminLessonVersionContentBlockListView(RoleBasedOutputMixin, APIView):
#     """
#     GET /lesson-versions/<uuid:lesson_version_id>/blocks/
#     POST /lesson-versions/<uuid:lesson_version_id>/blocks/
#     """
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

#     output_dto_public = ContentBlockPublicOutput
#     output_dto_admin = ContentBlockAdminOutput 

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.service = content_block_service

#     def get(self, request, lesson_version_id, *args, **kwargs):
#         """
#         Lấy danh sách các content block cho một lesson version.
#         """
#         try:
#             # Service trả về một list các domain entities 
#             blocks = self.service.list_blocks_for_version(
#                 lesson_version_id=lesson_version_id
#             )
#             return Response({"instance": blocks}, status=status.HTTP_200_OK)
        
#         except exceptions.LessonVersionNotFoundError:
#             raise Http404
#         except Exception as e:
#             logger.error(f"Error listing blocks: {e}", exc_info=True)
#             return Response(
#                 {"detail": "An unexpected error occurred."}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     def post(self, request, lesson_version_id, *args, **kwargs):
#         """
#         Tạo một content block mới cho một lesson version.
#         """
#         serializer = ContentBlockSerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
            
#             # Tạo Input DTO (Pydantic)
#             # DTO này có thể validate thêm (ví dụ: payload phải khớp với type)
#             create_dto = ContentBlockInput(**validated_data)

#             new_block = self.service.create_block(
#                 lesson_version_id=lesson_version_id,
#                 data=create_dto
#             )
            
#             # Trả về domain entity/DTO đã tạo
#             return Response({"instance": new_block}, status=status.HTTP_201_CREATED)

#         except ValidationError as e:
#             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
#         except (DomainError, exceptions.LessonVersionNotFoundError) as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error creating block: {e}", exc_info=True)
#             return Response(
#                 {"detail": "An unexpected error occurred."}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

# #=================================================================
# # API: admin/content-blocks/<uuid:pk>/
# #=================================================================
# class AdminContentBlockDetailView(RoleBasedOutputMixin, APIView):
#     """
#     GET admin/content-blocks/<uuid:pk>/
#     PATCH admin/content-blocks/<uuid:pk>/
#     DELETE admin/content-blocks/<uuid:pk>/
#     """
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

#     output_dto_public = ContentBlockPublicOutput
#     output_dto_admin = ContentBlockAdminOutput 

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.service = content_block_service

#     def get_object(self, pk):
#         """
#         Helper method để lấy block *model* từ DB.
#         Giống hệt cách bạn làm trong AdminUserDetailView.
#         """
#         try:
#             return ContentBlock.objects.get(pk=pk)
#         except ContentBlock.DoesNotExist:
#             raise Http404

#     def get(self, request, pk, *args, **kwargs):
#         """
#         Lấy chi tiết một content block.
#         """
#         # Service sẽ trả về một domain entity/DTO
#         try:
#             block = self.service.get_block_by_id(block_id=pk)
#             return Response({"instance": block})
#         except exceptions.ContentBlockNotFoundError:
#             raise Http404

#     def patch(self, request, pk, *args, **kwargs):
#         """
#         Cập nhật một phần (PATCH) một content block.
#         """
#         instance = self.get_object(pk)

#         serializer = ContentBlockSerializer(instance, data=request.data, partial=True)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
            
#             # Tạo Input DTO (loại partial)
#             update_dto = ContentBlockUpdateInput(**validated_data)
            
#             # Exclude 'None' hoặc 'unset' values
#             updates_payload = update_dto.model_dump(exclude_unset=True)
            
#             if not updates_payload:
#                 # Không có gì để update
#                 current_state = self.service.get_block_by_id(block_id=pk)
#                 return Response({"instance": current_state}, status=status.HTTP_200_OK)
            
#             updated_block = self.service.update_block(
#                 block_id=pk,
#                 updates=updates_payload
#             )
#             return Response({"instance": updated_block}, status=status.HTTP_200_OK)

#         except ValidationError as e:
#             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
#         except (DomainError, exceptions.ContentBlockNotFoundError) as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error PATCH block: {e}", exc_info=True)
#             return Response(
#                 {"detail": "An unexpected error occurred."}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     def delete(self, request, pk, *args, **kwargs):
#         """
#         Xóa một content block.
#         """
#         # get_object sẽ raise 404 nếu không tìm thấy
#         instance = self.get_object(pk) 
        
#         try:
#             self.service.delete_block(block_id=instance.id)
#             return Response(status=status.HTTP_204_NO_CONTENT)
        
#         except DomainError as e: # Ví dụ: "Không thể xóa block này"
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error DELETE block: {e}", exc_info=True)
#             return Response(
#                 {"detail": "An unexpected error occurred."}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

# #=================================================================
# # API: admin/lesson-versions/<uuid:lesson_version_id>/blocks/reorder/
# #=================================================================
# class AdminContentBlockReorderView(RoleBasedOutputMixin, APIView):
#     """
#     POST admin/lesson-versions/<uuid:lesson_version_id>/blocks/reorder/
    
#     Payload dự kiến:
#     {
#         "ordered_ids": ["uuid-1", "uuid-2", "uuid-3", ...]
#     }
#     """
#     permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

#     output_dto_public = ContentBlockPublicOutput
#     output_dto_admin = ContentBlockAdminOutput 

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.service = content_block_service

#     def post(self, request, lesson_version_id, *args, **kwargs):
#         """
#         Sắp xếp lại các content block.
#         """
#         serializer = ReorderBlocksSerializer(data=request.data)
        
#         try:
#             serializer.is_valid(raise_exception=True)
#             ordered_ids = serializer.validated_data["ordered_ids"]

#             self.service.reorder_blocks(
#                 lesson_version_id=lesson_version_id,
#                 ordered_ids=ordered_ids
#             )
            
#             return Response(
#                 {"detail": "Blocks reordered successfully."}, 
#                 status=status.HTTP_200_OK
#             )

#         except ValidationError as e:
#             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
#         except (DomainError, 
#                 exceptions.LessonVersionNotFoundError, 
#                 exceptions.BlockMismatchError) as e:
#             # BlockMismatchError: khi list ID không khớp với các block của version
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error reordering blocks: {e}", exc_info=True)
#             return Response(
#                 {"detail": "An unexpected error occurred."}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
        

# #=================================================================
# # API: instructor/lesson-versions/<uuid:lesson_version_id>/blocks/
# #=================================================================
# class InstructorLessonVersionContentBlockListView(RoleBasedOutputMixin, LessonPermissionMixin, APIView):
#     """
#     GET /instructor/lesson-versions/<uuid:lesson_version_id>/blocks/
#     POST /instructor/lesson-versions/<uuid:lesson_version_id>/blocks/
#     """
#     # Chỉ cần check IsAuthenticated, vì mixin sẽ check owner
#     permission_classes = [permissions.IsAuthenticated, IsInstructor]

#     output_dto_public = ContentBlockPublicOutput
#     output_dto_admin = ContentBlockAdminOutput 

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.service = content_block_service

#     def get(self, request, lesson_version_id, *args, **kwargs):
#         """
#         Lấy danh sách blocks (chỉ instructor/admin mới thấy).
#         """
#         # Kiểm tra quyền
#         self.check_lesson_permission(request, lesson_version_id)
        
#         try:
#             blocks = self.service.list_blocks_for_version(
#                 lesson_version_id=lesson_version_id
#             )
#             return Response({"instance": blocks}, status=status.HTTP_200_OK)
#         except exceptions.LessonVersionNotFoundError:
#             raise Http404 # Dòng này thực ra không cần, vì check_permission đã làm
#         except Exception as e:
#             # ... (Error handling y hệt admin) ...
#             logger.error(f"Error listing blocks: {e}", exc_info=True)
#             return Response({"detail": "An unexpected error occurred."}, 
#                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def post(self, request, lesson_version_id, *args, **kwargs):
#         """
#         Tạo block mới (chỉ instructor/admin).
#         """
#         # Kiểm tra quyền
#         self.check_lesson_version_permission(request, lesson_version_id)
        
#         serializer = ContentBlockSerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
#             create_dto = ContentBlockInput(**validated_data)

#             new_block = self.service.create_block(
#                 lesson_version_id=lesson_version_id,
#                 data=create_dto.to_dict() # Đảm bảo DTO được convert sang dict
#             )
#             return Response({"instance": new_block}, status=status.HTTP_201_CREATED)
#         except ValidationError as e:
#             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
#         except (DomainError, exceptions.LessonVersionNotFoundError) as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error creating block: {e}", exc_info=True)
#             return Response({"detail": "An unexpected error occurred."}, 
#                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# #=================================================================
# # API: /instructor/content-blocks/<uuid:pk>/
# #=================================================================
# class InstructorContentBlockDetailView(RoleBasedOutputMixin, ContentBlockPermissionMixin, APIView):
#     """
#     GET /instructor/content-blocks/<uuid:pk>/
#     PATCH /instructor/content-blocks/<uuid:pk>/
#     DELETE /instructor/content-blocks/<uuid:pk>/
#     """
#     permission_classes = [permissions.IsAuthenticated, IsInstructor]

#     output_dto_public = ContentBlockPublicOutput
#     output_dto_admin = ContentBlockAdminOutput 

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.service = content_block_service

#     def get(self, request, pk, *args, **kwargs):
#         """
#         Lấy chi tiết block (chỉ instructor/admin).
#         """
#         # Kiểm tra quyền
#         self.check_content_block_permission(request, pk)
        
#         try:
#             block = self.service.get_block_by_id(block_id=pk)
#             return Response({"instance": block})
#         except exceptions.ContentBlockNotFoundError:
#             raise Http404 # Dòng này thực ra không cần

#     def patch(self, request, pk, *args, **kwargs):
#         """
#         Cập nhật block (chỉ instructor/admin).
#         """
#         # Kiểm tra quyền VÀ lấy instance
#         instance = self.check_content_block_permission(request, pk)
        
#         serializer = ContentBlockSerializer(instance, data=request.data, partial=True)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
#             update_dto = ContentBlockUpdateInput(**validated_data)
#             updates_payload = update_dto.model_dump(exclude_unset=True)
            
#             if not updates_payload:
#                 current_state = self.service.get_block_by_id(block_id=pk)
#                 return Response({"instance": current_state}, status=status.HTTP_200_OK)
            
#             updated_block = self.service.update_block(
#                 block_id=pk,
#                 updates=updates_payload
#             )
#             return Response({"instance": updated_block}, status=status.HTTP_200_OK)
#         except ValidationError as e:
#             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
#         except (DomainError, exceptions.ContentBlockNotFoundError) as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error PATCH block: {e}", exc_info=True)
#             return Response({"detail": "An unexpected error occurred."}, 
#                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def delete(self, request, pk, *args, **kwargs):
#         """
#         Xóa block (chỉ instructor/admin).
#         """
#         # Kiểm tra quyền VÀ lấy instance
#         instance = self.check_content_block_permission(request, pk)
        
#         try:
#             self.service.delete_block(block_id=instance.id)
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         except DomainError as e: 
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error DELETE block: {e}", exc_info=True)
#             return Response({"detail": "An unexpected error occurred."}, 
#                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #=================================================================
# # API: /instructor/lesson-versions/<uuid:lesson_version_id>/blocks/reorder/
# #=================================================================
# class InstructorContentBlockReorderView(RoleBasedOutputMixin, LessonPermissionMixin, APIView):
#     """
#     POST /instructor/lesson-versions/<uuid:lesson_version_id>/blocks/reorder/
#     """
#     permission_classes = [permissions.IsAuthenticated, IsInstructor]

#     output_dto_public = ContentBlockPublicOutput
#     output_dto_admin = ContentBlockAdminOutput 

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.service = content_block_service

#     def post(self, request, lesson_version_id, *args, **kwargs):
#         """
#         Sắp xếp lại blocks (chỉ instructor/admin).
#         """
#         # Kiểm tra quyền
#         self.check_lesson_permission(request, lesson_version_id)

#         serializer = ReorderBlocksSerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             ordered_ids = serializer.validated_data["ordered_ids"]

#             self.service.reorder_blocks(
#                 lesson_version_id=lesson_version_id,
#                 ordered_ids=ordered_ids
#             )
#             return Response({"detail": "Blocks reordered successfully."}, 
#                             status=status.HTTP_200_OK)
#         except ValidationError as e:
#             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
#         except (DomainError, 
#                 exceptions.LessonVersionNotFoundError, 
#                 exceptions.BlockMismatchError) as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error reordering blocks: {e}", exc_info=True)
#             return Response({"detail": "An unexpected error occurred."}, 
#                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstructorContentBlockListCreateView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /instructor/lessons/{lesson_id}/blocks/ - List content blocks
    POST /instructor/lessons/{lesson_id}/blocks/ - Tạo content block mới
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor, IsCourseOwner]
    
    # Permission check sẽ tự động tìm Lesson dựa vào lesson_id trong URL
    # và check quyền trên Course chứa Lesson đó (IsCourseOwner)
    permission_lookup = {'lesson_id': Lesson}

    # Định nghĩa Output DTO (để Mixin tự format response)
    output_dto_public = ContentBlockPublicOutput
    output_dto_admin = ContentBlockAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inject service (đã được refactor ở bước trước)
        self.content_block_service = content_block_service

    def get(self, request, lesson_id: uuid.UUID, *args, **kwargs):
        """List tất cả blocks trong lesson (Sắp xếp theo position)"""
        try:
            blocks_list = self.content_block_service.get_content_blocks(
                lesson_id=lesson_id,
            )
            return Response({"instance": blocks_list}, status=status.HTTP_200_OK)
            
        except Lesson.DoesNotExist:
            return Response(
                {"detail": "Bài học không tồn tại."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # logger.error(f"Lỗi khi lấy danh sách block: {e}", exc_info=True)
            return Response(
                {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, lesson_id: uuid.UUID, *args, **kwargs):
        """
        Tạo ContentBlock mới.
        Hỗ trợ: Text, Video, Quiz, File... (xử lý qua Service Router)
        """
        # 1. Validate định dạng Input thô (DRF Serializer)
        serializer = ContentBlockCreateSerializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Convert sang DTO & Validate Logic (Pydantic)
        try:
            # DTO này nên validate cấu trúc của field 'payload' dựa trên 'type'
            block_dto = ContentBlockInput(**validated_data)
        except Exception as e:
            return Response(
                {"detail": f"Dữ liệu payload không hợp lệ: {e}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Gọi Service
        try:
            # Lưu ý: Cần truyền 'actor' (request.user) để Service commit file
            new_block = self.content_block_service.create_content_block(
                lesson_id=lesson_id,
                data=block_dto.model_dump(), # hoặc .dict() tùy phiên bản Pydantic
                actor=request.user
            )
            
            return Response({"instance": new_block}, status=status.HTTP_201_CREATED)
            
        except Lesson.DoesNotExist:
            return Response(
                {"detail": "Bài học không tồn tại."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            # Bắt các lỗi logic validation từ Service (ví dụ: Quiz tạo lỗi)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # logger.error(f"Lỗi khi tạo content block: {e}", exc_info=True)
            return Response(
                {"detail": f"Lỗi máy chủ: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class InstructorContentBlockDetailView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET    /instructor/blocks/{block_id}/  - Lấy chi tiết
    PUT    /instructor/blocks/{block_id}/  - Cập nhật (Content, Title, File)
    DELETE /instructor/blocks/{block_id}/  - Xóa block
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor, IsCourseOwner]
    
    # Permission check: Block -> Lesson -> Module -> Course -> Owner
    permission_lookup = {'block_id': ContentBlock}

    output_dto_public = ContentBlockPublicOutput
    output_dto_admin = ContentBlockAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content_block_service = content_block_service

    def get(self, request, block_id: uuid.UUID, *args, **kwargs):
        """Lấy chi tiết 1 block"""
        try:
            block_detail = self.content_block_service.get_content_block_detail(
                block_id=block_id
            )
            return Response({"instance": block_detail}, status=status.HTTP_200_OK)
            
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": f"Lỗi server - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, block_id: uuid.UUID, *args, **kwargs):
        """
        Update Block.
        Hỗ trợ partial update (gửi field nào update field đó).
        """
        # 1. Validate Input (Dùng partial=True vì có thể chỉ update title hoặc payload)
        serializer = ContentBlockUpdateSerializer(data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Gọi Service
        try:
            updated_block = self.content_block_service.update_content_block(
                block_id=block_id,
                data=validated_data,
                actor=request.user # Cần actor để commit file nếu có
            )
            
            return Response(
                {"instance": updated_block, "detail": "Cập nhật thành công."}, 
                status=status.HTTP_200_OK
            )

        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # logger.error(...)
            return Response({"detail": f"Lỗi hệ thống: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, block_id: uuid.UUID, *args, **kwargs):
        """Xóa Block"""
        try:
            self.content_block_service.delete_content_block(block_id=block_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except DomainError as e:
            # Idempotent: Nếu không tìm thấy thì coi như đã xóa, hoặc báo 404 tùy logic
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": f"Lỗi hệ thống: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class InstructorContentBlockConvertView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    POST /instructor/blocks/{block_id}/convert/
    Chuyển đổi loại block (Ví dụ: Text -> Video).
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor, IsCourseOwner]
    
    # Vẫn cần check quyền sở hữu block
    permission_lookup = {'block_id': ContentBlock}

    output_dto_public = ContentBlockPublicOutput
    output_dto_admin = ContentBlockAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content_block_service = content_block_service

    def post(self, request, block_id: uuid.UUID, *args, **kwargs):
        # 1. Validate Input (Chỉ cần target_type)
        serializer = ConvertBlockSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            target_type = serializer.validated_data['target_type']
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Gọi Service Convert
        try:
            new_block_domain = self.content_block_service.convert_content_block(
                block_id=block_id,
                target_type=target_type,
                actor=request.user # Cần actor để tạo Quiz mới nếu target_type='quiz'
            )

            return Response(
                {
                    "instance": new_block_domain, 
                    "detail": f"Đã chuyển đổi sang {target_type}."
                }, 
                status=status.HTTP_200_OK
            )

        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Lỗi hệ thống: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class InstructorContentBlockReorderView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    PUT /instructor/lessons/<uuid:lesson_id>/blocks/reorder/
    Sắp xếp lại vị trí các content block trong một bài học.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor, IsCourseOwner]
    
    # Permission check: Tự động tìm Lesson theo lesson_id và check owner của Course chứa nó
    permission_lookup = {'lesson_id': Lesson}

    output_dto_public = ContentBlockPublicOutput 
    output_dto_admin = ContentBlockAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content_block_service = content_block_service

    def put(self, request, lesson_id: uuid.UUID, *args, **kwargs):
        # 1. Validate Input
        serializer = ContentBlockReorderSerializer(data=request.data)
        
        # Bắt lỗi validate cơ bản (sai format UUID, list rỗng...)
        try:
            serializer.is_valid(raise_exception=True)
            block_ids = serializer.validated_data['block_ids']
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Gọi Service
        try:
            sorted_blocks = self.content_block_service.reorder_content_blocks(
                lesson_id=lesson_id,
                block_id_list=block_ids
            )

            return Response(
                {"instance": sorted_blocks, "detail": "Sắp xếp nội dung thành công."}, 
                status=status.HTTP_200_OK
            )

        except DomainError as e:
            # Lỗi business (ví dụ: gửi thiếu ID, ID lạ)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # Lỗi hệ thống không mong muốn
            return Response(
                {"detail": f"Lỗi hệ thống: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )