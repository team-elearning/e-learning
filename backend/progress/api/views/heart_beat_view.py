# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
from pydantic import ValidationError as PydanticValidationError
import logging

from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin
from core.api.permissions import CanViewCourseContent
from progress.services import tracking_service
from progress.api.dtos.heart_beat_dto import BlockHeartbeatInput, BlockProgressPublicOutput, BlockProgressAdminOutput, BlockCompletionInput, CourseResumeAdminOutput, CourseResumePublicOutput
from progress.serializers import BlockHeartbeatSerializer, BlockCompletionInputSerializer
from content.models import ContentBlock



logger = logging.getLogger(__name__)

class BlockInteractionHeartbeatView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /tracking/heartbeat/?block_id=... 
        -> Lấy vị trí cũ để RESUME (Tiếp tục xem).

    POST /tracking/heartbeat/
    API nhận tín hiệu 'nhịp tim' từ client để lưu vị trí video/pdf.
    Nên gọi API này mỗi 5-10s hoặc sự kiện onPause, onDestroy phía Client.
    """
    permission_classes = [IsAuthenticated, CanViewCourseContent] 

    permission_lookup = {'block_id': ContentBlock}

    output_dto_public = BlockProgressPublicOutput
    output_dto_admin = BlockProgressAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Khởi tạo service (hoặc inject dependency nếu dùng container)
        self.interaction_service = tracking_service

    def get(self, request, *args, **kwargs):
        """
        Lấy trạng thái của user tại block_id được gửi lên.
        Client dùng dữ liệu này để 'seek' video tới đúng giây user đã dừng lại.
        """
        block_id = request.query_params.get('block_id')

        if not block_id:
            return Response(
                {"detail": "Thiếu block id."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Gọi service lấy dữ liệu
            user_block_progress_domain = self.interaction_service.get_interaction_status(
                user=request.user, 
                block_id=block_id
            )
            return Response({"instance": user_block_progress_domain}, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong BlockInteractionHeartbeatView (GET): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi lấy tiến độ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        """
        Payload mẫu:
        {
            "block_id": "uuid-cua-block",
            "interaction_data": {
                "video_timestamp": 145.5,
                "playback_rate": 1.5
            }
        }
        """
        serializer = BlockHeartbeatSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
        # 2. Gọi Service để xử lý logic nghiệp vụ
        try:
             # request.data map thẳng vào model Pydantic
            dto = BlockHeartbeatInput(**validated_data)

            user_block_progress_domain = self.interaction_service.sync_heartbeat(
                user=request.user,
                data=dto.model_dump()
            )
            
            # Return 200 OK rỗng để tiết kiệm băng thông (Heartbeat cần nhẹ)
            return Response({"status": "synced", "is_completed": user_block_progress_domain.is_completed}, status=status.HTTP_200_OK)
        
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError:
            return Response({"detail": "Chưa ghi danh."}, status=403)

        except ValueError as e:
            # Lỗi logic (ví dụ block không tồn tại)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # Lỗi hệ thống
            logger.error(f"Lỗi trong BlockInteractionHeartbeatView (POST): {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi đồng bộ tiến độ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class BlockCompletionView(RoleBasedOutputMixin, APIView):
    """
    POST /tracking/complete/
    Đánh dấu một block là hoàn thành (Tick xanh).
    Logic kiểm tra điều kiện (Video > 90%, Time scroll) sẽ nằm ở Service Layer.
    """
    permission_classes = [IsAuthenticated]

    # Dùng lại Output DTO của bạn để trả về trạng thái mới nhất
    output_dto_public = BlockProgressPublicOutput
    output_dto_admin = BlockProgressAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interaction_service = tracking_service  # Inject Service

    def post(self, request, *args, **kwargs):
        serializer = BlockCompletionInputSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

        except Exception as e:
            return Response({"detail": f"Dữ liệu không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            input_dto = BlockCompletionInput(**serializer.validated_data)

            # Gọi Service để xử lý logic nghiệp vụ phức tạp
            # Service sẽ trả về instance UserBlockProgress đã update
            updated_progress = self.interaction_service.mark_block_as_complete(
                user=request.user,
                data=input_dto.model_dump()
            )

            return Response(
                {"detail": "Đã đánh dấu hoàn thành.", "instance": updated_progress},
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            # Lỗi nghiệp vụ (ví dụ: chưa đủ điều kiện hoàn thành)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Lỗi trong BlockCompletionView: {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CourseResumeView(RoleBasedOutputMixin, APIView):
    """
    GET /tracking/resume/<course_id>/
    Trả về ResumePositionDomain để Frontend redirect user.
    """
    permission_classes = [IsAuthenticated]
    
    # Bạn cần định nghĩa Output Serializer cho Domain này
    output_dto_public = CourseResumePublicOutput
    output_dto_admin = CourseResumeAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interaction_service = tracking_service

    def get(self, request, course_id, *args, **kwargs):
        try:
            # Gọi Service -> Nhận Domain Object
            resume_domain = self.interaction_service.get_course_resume_position(
                user=request.user,
                course_id=course_id
            )

            if not resume_domain:
                return Response(
                    {"detail": "Khóa học chưa có nội dung."}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response({"instance": resume_domain}, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Lỗi Resume Course {course_id}: {e}", exc_info=True)
            return Response({"detail": "Lỗi server."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)