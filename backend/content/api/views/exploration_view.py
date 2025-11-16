import logging
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied

from content.api.mixins import RoleBasedOutputMixin, ExplorationPermissionMixin
from content.services.exceptions import DomainError 
from content.models import Exploration
from content.services import exploration_service 
from content.serializers import ExplorationCreateSerializer, ExplorationMetadataSerializer
from content.api.dtos.exploration_dto import ( 
    ExplorationCreateInput,
    UpdateExplorationMetadataInput,
    ExplorationListOutput,
    ExplorationPublicOutput,
    ExplorationAdminOutput
)
from content.api.permissions import IsInstructor # <-- Permission tùy chỉnh



logger = logging.getLogger(__name__)

class PublicExplorationListView(RoleBasedOutputMixin, APIView):
    """
    GET /explorations/
    API công khai, chỉ đọc, chỉ lấy các explorations đã published.
    """
    permission_classes = [permissions.AllowAny]
    
    # Dùng DTO list
    output_dto_public = ExplorationListOutput
    output_dto_admin = ExplorationListOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exploration_service = exploration_service

    def get(self, request):
        try:
            explorations = self.exploration_service.get_published_explorations()
            return Response({"instance": explorations}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Lỗi khi lấy public explorations: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PublicExplorationDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /explorations/<str:id>/
    API công khai, chỉ đọc, chỉ lấy exploration đã published.
    """
    permission_classes = [permissions.AllowAny]
    
    # Dùng DTO chi tiết
    output_dto_public = ExplorationPublicOutput
    output_dto_admin = ExplorationAdminOutput 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exploration_service = exploration_service

    def get(self, request, id):
        try:
            # Service đã có logic kiểm tra "published" và "permission"
            exploration_domain = self.exploration_service.get_full_exploration_details(
                exploration_id=id, 
                user=request.user if request.user.is_authenticated else None
            )
            return Response({"instance": exploration_domain})
        except (DomainError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exploration.DoesNotExist:
             return Response({"detail": "Exploration not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Lỗi khi lấy public exploration detail {id}: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class InstructorExplorationListView(RoleBasedOutputMixin, APIView):
    """
    GET /api/v1/instructor/explorations/ (Lấy explorations của TÔI)
    POST /api/v1/instructor/explorations/ (Tạo exploration mới)
    """
    permission_classes = [permissions.IsAuthenticated] # Phải đăng nhập

    output_dto_public = ExplorationListOutput # Sẽ không dùng
    output_dto_admin = ExplorationListOutput # Dùng DTO list

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exploration_service = exploration_service

    def get(self, request):
        """ Lấy danh sách explorations do user này sở hữu (cả draft). """
        try:
            # Service mới: Lấy bài của owner
            explorations = self.exploration_service.get_explorations_for_owner(request.user)
            return Response({"instance": explorations}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Lỗi khi lấy instructor explorations: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """ Tạo một exploration mới (giống hệt code cũ của bạn). """
        serializer = ExplorationCreateSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        try:
            input_dto = ExplorationCreateInput(**serializer.validated_data)
        except Exception as e:
            return Response({"detail": f"Dữ liệu đầu vào không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_exploration = self.exploration_service.create_exploration(
                owner=request.user, 
                data=input_dto.to_dict()
            )
            # Trả về DTO chi tiết
            self.output_dto_admin = ExplorationAdminOutput
            return Response({"instance": new_exploration}, status=status.HTTP_201_CREATED)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi khi tạo exploration: {e}", exc_info=True)
            return Response({"detail": "Lỗi hệ thống khi tạo."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstructorExplorationDetailView(RoleBasedOutputMixin, ExplorationPermissionMixin, APIView):
    """
    API cho Instructor/Admin quản lý 1 exploration cụ thể.
    (Hợp nhất DetailView và MetadataUpdateView)
    
    GET /instructor/explorations/<str:id>/
    PATCH /instructor/explorations/<str:id>/
    DELETE /instructor/explorations/<str:id>/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    output_dto_public = ExplorationPublicOutput
    output_dto_admin = ExplorationAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exploration_service = exploration_service

    def get(self, request, id):
        """ Lấy chi tiết (cho owner/admin). """
        try:
            # Dùng mixin để check quyền và lấy object
            exploration = self.check_exploration_permission(request, id)
            
            # Service lấy chi tiết đầy đủ (states, v.v.)
            exploration_domain = self.exploration_service.get_full_exploration_details(
                exploration_id=id, 
                user=request.user
            )
            return Response({"instance": exploration_domain})
        except (Http404, DomainError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND if isinstance(e, Http404) else status.HTTP_403_FORBIDDEN)

    def put(self, request, id):
        """ Cập nhật TOÀN BỘ (owner/admin). """
        try:
            exploration_instance = self.check_exploration_permission(request, id)
            full_json_data = request.data
            
            updated_exploration = self.exploration_service.update_full_exploration(
                exploration=exploration_instance, 
                full_data=full_json_data,
                user=request.user
            )
            return Response({"instance": updated_exploration}, status=status.HTTP_200_OK)
        except (Http404, DomainError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        """ Cập nhật METADATA (owner/admin). """
        try:
            instance = self.check_exploration_permission(request, id)
        except (Http404, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND if isinstance(e, Http404) else status.HTTP_403_FORBIDDEN)

        serializer = ExplorationMetadataSerializer(instance, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        try:
            update_dto = UpdateExplorationMetadataInput(**serializer.validated_data)
        except Exception as e:
            return Response({"detail": f"Dữ liệu đầu vào không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        updates_payload = update_dto.model_dump(exclude_unset=True)
        if not updates_payload:
            return Response({"instance": instance}, status=status.HTTP_200_OK)

        try:
            updated_exploration = self.exploration_service.update_exploration_metadata(
                exploration=instance,
                updates=updates_payload
            )
            return Response({"instance": updated_exploration}, status=status.HTTP_200_OK)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        """ Xóa (owner/admin). """
        try:
            exploration_instance = self.check_exploration_permission(request, id)
            
            self.exploration_service.delete_exploration(
                exploration=exploration_instance, 
                user=request.user
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (Http404, DomainError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

# class ExplorationListView(RoleBasedOutputMixin, APIView):
#     """
#     GET /explorations/
#     POST /explorations/
#     """
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]

#     # Định nghĩa DTOs cho RoleBasedOutputMixin
#     # Cả public và admin đều thấy cùng một danh sách
#     output_dto_public = ExplorationListOutput
#     output_dto_admin = ExplorationListOutput

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Inject service giống như bạn làm
#         self.exploration_service = exploration_service

#     def get(self, request):
#         """
#         Lấy danh sách các exploration (đã published).
#         """
#         try:
#             # Service trả về một list các domain/model instances
#             explorations = self.exploration_service.get_published_explorations()
            
#             # Trả về list instances, mixin sẽ xử lý
#             return Response({"instance": explorations}, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             logger.error(f"Lỗi khi lấy danh sách exploration: {e}", exc_info=True)
#             return Response(
#                 {"detail": f"Đã xảy ra lỗi: {str(e)}"}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

#     def post(self, request):
#         """
#         Tạo một exploration mới.
#         """
#         # 1. Validate định dạng thô bằng DRF Serializer
#         serializer = ExplorationCreateSerializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
#         except ValidationError as e:
#             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

#         # 2. Tạo Input DTO để validate nghiệp vụ
#         try:
#             input_dto = ExplorationCreateInput(**validated_data)
#         except Exception as e: # Lỗi Pydantic validation
#             return Response({"detail": f"Dữ liệu đầu vào không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#         # 3. Gọi Service với payload sạch
#         try:
#             new_exploration = self.exploration_service.create_exploration(
#                 owner=request.user, 
#                 data=input_dto.to_dict() # Dùng to_dict() giống 'RegisterView'
#             )
            
#             # 4. Trả về instance, mixin sẽ dùng DTO chi tiết (Admin) để serialize
#             # (Chúng ta cần đổi DTOs cho POST response)
            
#             # Giải pháp: Set DTOs chi tiết tạm thời cho mixin
#             self.output_dto_public = ExplorationPublicOutput
#             self.output_dto_admin = ExplorationAdminOutput
            
#             return Response({"instance": new_exploration}, status=status.HTTP_201_CREATED)
        
#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi khi tạo exploration: {e}", exc_info=True)
#             return Response({"detail": "Lỗi hệ thống khi tạo exploration."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class ExplorationDetailView(RoleBasedOutputMixin, APIView):
#     """
#     GET /explorations/<str:id>/
#     PUT /explorations/<str:id>/
#     DELETE /explorations/<str:id>/
#     """
#     permission_classes = [IsOwnerOrAdminOrReadOnly]

#     # Định nghĩa DTOs chi tiết cho mixin
#     output_dto_public = ExplorationPublicOutput
#     output_dto_admin = ExplorationAdminOutput

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.exploration_service = exploration_service

#     def get_object(self, request, id):
#         """
#         Helper để lấy object và kiểm tra quyền.
#         """
#         try:
#             obj = Exploration.objects.get(pk=id)
#         except Exploration.DoesNotExist:
#             raise Http404
        
#         # Kiểm tra quyền sở hữu object
#         self.check_object_permissions(request, obj)
#         return obj

#     def get(self, request, id):
#         """
#         Lấy data chi tiết (toàn bộ) của exploration.
#         """
#         exploration_instance = self.get_object(request, id)
        
#         try:
#             # Service có thể lấy thêm states/media... nếu DTO yêu cầu
#             # Hoặc Pydantic (với from_attributes=True) sẽ tự động lazy-load
#             return Response({"instance": exploration_instance})
            
#         except Exception as e:
#             logger.error(f"Lỗi khi lấy chi tiết exploration {id}: {e}", exc_info=True)
#             return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def put(self, request, id):
#         """
#         (TRƯỜNG HỢP ĐẶC BIỆT)
#         Lưu toàn bộ JSON exploration từ editor.
#         Luồng này KHÔNG dùng Serializer -> DTO như bình thường.
#         """
#         exploration_instance = self.get_object(request, id)
#         full_json_data = request.data
        
#         # Bỏ qua Serializer và Input DTO, gọi thẳng service
#         try:
#             updated_exploration = self.exploration_service.update_full_exploration(
#                 exploration=exploration_instance, 
#                 full_data=full_json_data,
#                 user=request.user
#             )
            
#             # Trả về instance đã cập nhật, mixin sẽ serialize
#             return Response({"instance": updated_exploration}, status=status.HTTP_200_OK)

#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi khi PUT exploration {id}: {e}", exc_info=True)
#             return Response({"detail": f"Lỗi khi cập nhật: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def delete(self, request, id):
#         """
#         Xóa một exploration.
#         """
#         exploration_instance = self.get_object(request, id)
        
#         try:
#             # Gọi service để xử lý logic xóa
#             self.exploration_service.delete_exploration(
#                 exploration=exploration_instance, 
#                 user=request.user
#             )
#             return Response(status=status.HTTP_204_NO_CONTENT)
            
#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi khi DELETE exploration {id}: {e}", exc_info=True)
#             return Response({"detail": "Lỗi hệ thống khi xóa."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class ExplorationMetadataUpdateView(RoleBasedOutputMixin, APIView):
#     """
#     PATCH /api/v1/explorations/<str:id>/metadata/
#     """
#     permission_classes = [IsOwnerOrAdminOrReadOnly]
    
#     # Dùng DTOs chi tiết vì chúng ta đang trả về object đầy đủ
#     output_dto_public = ExplorationPublicOutput
#     output_dto_admin = ExplorationAdminOutput

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.exploration_service = exploration_service

#     def get_object(self, request, id):
#         try:
#             obj = Exploration.objects.get(pk=id)
#         except Exploration.DoesNotExist:
#             raise Http404
#         self.check_object_permissions(request, obj)
#         return obj

#     def patch(self, request, id):
#         """
#         Cập nhật metadata (theo đúng flow của AdminUserDetailView).
#         """
#         instance = self.get_object(request, id)

#         # Validate định dạng thô bằng DRF Serializer
#         serializer = ExplorationMetadataSerializer(instance, data=request.data, partial=True)
#         try:
#             serializer.is_valid(raise_exception=True)
#             validated_data = serializer.validated_data
#         except ValidationError as e:
#             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

#         # Tạo Input DTO để validate nghiệp vụ
#         try:
#             update_dto = UpdateExplorationMetadataInput(**validated_data)
#         except Exception as e: # Lỗi Pydantic
#             return Response({"detail": f"Dữ liệu đầu vào không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
#         # Lấy payload (chỉ các trường được gửi lên)
#         updates_payload = update_dto.model_dump(exclude_unset=True)
        
#         if not updates_payload:
#             return Response({"instance": instance}, status=status.HTTP_200_OK)

#         try:
#             updated_exploration = self.exploration_service.update_exploration_metadata(
#                 exploration=instance,
#                 updates=updates_payload
#             )
            
#             return Response({"instance": updated_exploration}, status=status.HTTP_200_OK)
            
#         except DomainError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi khi PATCH metadata {id}: {e}", exc_info=True)
#             return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)