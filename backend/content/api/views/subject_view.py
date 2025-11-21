# Cần import các thành phần này
import logging
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from content.services import subject_service 
from content.serializers import SubjectSerializer 
from content.api.dtos.subject_dto import SubjectInput, UpdateSubjectInput, SubjectAdminOutput, SubjectPublicOutput
from core.api.mixins import RoleBasedOutputMixin 
from core.exceptions import DomainError      



# Khởi tạo logger
logger = logging.getLogger(__name__)

class AdminSubjectListView(RoleBasedOutputMixin, APIView):
    """
    GET /api/subjects/     (admin) - List all subjects
    POST /api/subjects/    (admin) - Create a new subject
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    # Cấu hình output DTOs cho RoleBasedOutputMixin
    output_dto_public = SubjectPublicOutput
    output_dto_admin = SubjectAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tiêm (inject) service
        self.subject_service = subject_service

    def get(self, request):
        """
        Handles GET requests to list all subjects.
        """
        try:
            # Service trả về một list các domain entities (hoặc DTOs)
            subjects = self.subject_service.list_all_subjects()
            
            # Mixin sẽ tự động serialize 'subjects' dựa trên vai trò user
            return Response({"instance": subjects}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Unexpected error in AdminSubjectListView (GET): {e}", exc_info=True)
            return Response(
                {"detail": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to create a new subject.
        """
        
        # 1. Validate định dạng input thô (dùng DRF Serializer)
        serializer = SubjectSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            # Trả về lỗi validation của DRF
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Tạo Input DTO từ dữ liệu đã validate
        try:
            # DTO này xử lý validation logic sâu hơn (ví dụ: Pydantic)
            subject_create_dto = SubjectInput(**validated_data)
        except Exception as e: # Bắt lỗi Pydantic validation
            return Response({"detail": f"Invalid input data: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Gọi Service để thực thi logic nghiệp vụ
        try:
            new_subject = self.subject_service.create_subject(
                data=subject_create_dto.model_dump() # Dùng model_dump() cho Pydantic v2+
            )
            
            # Trả về instance đã được tạo
            return Response(
                {"instance": new_subject}, 
                status=status.HTTP_201_CREATED
            )
        
        # 4. Xử lý các lỗi nghiệp vụ (ví dụ: "Slug đã tồn tại")
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # 5. Xử lý các lỗi hệ thống khác
        except Exception as e:
            logger.error(f"Unexpected error in AdminSubjectListView (POST): {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred during subject creation."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminSubjectDetailView(RoleBasedOutputMixin, APIView):
    """
    GET    /api/v1/subjects/<uuid:pk>/ (admin) - Retrieve a subject
    PUT    /api/v1/subjects/<uuid:pk>/ (admin) - Update a subject
    PATCH  /api/v1/subjects/<uuid:pk>/ (admin) - Partially update a subject
    DELETE /api/v1/subjects/<uuid:pk>/ (admin) - Delete a subject
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    output_dto_public = SubjectPublicOutput
    output_dto_admin = SubjectAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject_service = subject_service

    def get(self, request, pk):
        """
        Handles GET requests to retrieve a single subject by its UUID.
        """
        try:
            subject = self.subject_service.get_subject_by_id(subject_id=pk)
            return Response({"instance": subject}, status=status.HTTP_200_OK)
        except DomainError as e: # Lỗi nghiệp vụ (ví dụ: "Not found")
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving subject {pk}: {e}", exc_info=True)
            return Response({"detail": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        """
        Handles PUT requests for a full update of a subject.
        """
        # 1. Validate (giống POST)
        serializer = SubjectSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Tạo DTO (giống POST)
        try:
            update_dto = SubjectInput(**validated_data)
        except Exception as e:
            return Response({"detail": f"Invalid input data: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Gọi Service
        try:
            updated_subject = self.subject_service.update_subject(
                subject_id=pk,
                updates=update_dto.model_dump() # Gửi payload đầy đủ
            )
            return Response({"instance": updated_subject}, status=status.HTTP_200_OK)
        except DomainError as e: # "Not found" hoặc "Validation error"
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in AdminSubjectDetailView (PUT) for {pk}: {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        """
        Handles PATCH requests for a partial update, theo cấu trúc của CurrentUserDetailView.
        """
        # 1. Validate (dùng partial=True)
        # Lưu ý: Chúng ta không cần lấy instance ở đây, service sẽ làm việc đó.
        serializer = SubjectSerializer(data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Tạo DTO từ dữ liệu đã validate
        # Dùng một DTO riêng cho update, nơi các trường đều là Optional
        update_dto = UpdateSubjectInput(**validated_data)

        # 3. Tạo payload, loại bỏ các giá trị 'None'
        updates_payload = update_dto.model_dump(exclude_none=True)

        # 4. Nếu payload rỗng, chỉ cần trả về đối tượng hiện tại
        if not updates_payload:
            try:
                current_subject = self.subject_service.get_subject_by_id(subject_id=pk)
                return Response({"instance": current_subject}, status=status.HTTP_200_OK)
            except DomainError as e:
                return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        # 5. Gọi Service với payload đã được lọc
        try:
            updated_subject = self.subject_service.update_subject(
                subject_id=pk,
                updates=updates_payload # Gửi payload từng phần
            )
            return Response({"instance": updated_subject}, status=status.HTTP_200_OK)
        except DomainError as e: # "Not found" hoặc "Validation error"
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in AdminSubjectDetailView (PATCH) for {pk}: {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        """
        Handles DELETE requests to remove a subject.
        """
        try:
            self.subject_service.delete_subject(subject_id=pk)
            # Trả về 204 No Content khi xóa thành công
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DomainError as e: # Lỗi nghiệp vụ (ví dụ: "Not found")
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting subject {pk}: {e}", exc_info=True)
            return Response({"detail": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)