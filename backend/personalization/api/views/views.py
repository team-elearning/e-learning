from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError as DRFValidationError
from pydantic import ValidationError as PydanticValidationError
import logging

# Import Mixins của bạn
from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin # Giả định path
from personalization.services import ai_recommendation_service 
from personalization.api.dtos.ai_sync_dto import AISyncResultOutput, AISyncInput
from personalization.api.dtos.ai_recommendation_dto import AIRecommendationInput
from personalization.serializers import AISyncSerializer, AIRecommendationQuerySerializer
from content.api.dtos.course_dto import CourseCatalogPublicOutput 



logger = logging.getLogger(__name__)

class AISyncView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    POST /content/ai/sync/
    -> Trigger việc tính toán vector cho các khóa học.
    """
    permission_classes = [IsAuthenticated] 
    
    # Mixin configuration
    output_dto_public = AISyncResultOutput
    output_dto_admin = AISyncResultOutput # Admin hay User thấy output giống nhau
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_service = ai_recommendation_service

    def post(self, request, *args, **kwargs):
        """
        Luồng: Serializer -> DTO Input -> Service -> Domain -> DTO Output (Mixin)
        """
        # 1. Serializer Validation
        serializer = AISyncSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Map sang Pydantic DTO Input
        try:
            dto_input = AISyncInput(**validated_data)
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Gọi Service & Trả về Domain Object
        try:
            sync_result_domain = self.ai_service.sync_course_embeddings(
                force_update=dto_input.force_update
            )
            
            # Mixin sẽ tự động lấy `output_dto_...` để map `sync_result_domain` thành JSON
            return Response({"instance": sync_result_domain}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Lỗi trong AISyncView (POST): {e}", exc_info=True)
            return Response({"detail": f"Lỗi server: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIRecommendationView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /content/ai/suggest/?q=...&top_n=5
    -> Gợi ý khóa học dựa trên ngữ nghĩa.
    """
    permission_classes = [AllowAny] 
    
    # Output là danh sách khóa học, tái sử dụng DTO Public của Course
    output_dto_public = CourseCatalogPublicOutput
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_service = ai_recommendation_service

    def get(self, request, *args, **kwargs):
        """
        Luồng GET: Serializer (Query params) -> Service -> Domain List -> DTO Output
        """
        # 1. Validate Query Params bằng Serializer
        serializer = AIRecommendationQuerySerializer(data=request.query_params)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. (Optional) Map sang DTO Input nếu logic phức tạp, 
        # hoặc truyền thẳng vào service nếu đơn giản.
        # Ở đây làm chuẩn chỉ theo yêu cầu của bạn:
        try:
            dto_input = AIRecommendationInput(**validated_data)
        except PydanticValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Gọi Service lấy List Domain (QuerySet Course)
        try:
            courses_list_domain = self.ai_service.suggest_courses(
                q=dto_input.q,
                top_n=dto_input.top_n
            )
            
            # Trả về instance dạng list, Mixin sẽ serialize từng phần tử
            return Response({"instance": courses_list_domain}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Lỗi trong AIRecommendationView (GET): {e}", exc_info=True)
            return Response({"detail": f"Lỗi server: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)