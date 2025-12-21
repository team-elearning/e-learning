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
from progress.services import course_tracking_service
from progress.api.dtos.heart_beat_dto import BlockHeartbeatInput, BlockProgressPublicOutput, BlockProgressAdminOutput, ResetProgressOutput, CourseProgressPublicOutput
from progress.serializers import BlockHeartbeatSerializer, BlockCompletionInputSerializer
from content.models import ContentBlock, Course, Enrollment



logger = logging.getLogger(__name__)

class BlockInteractionHeartbeatView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /tracking/heartbeat/blocks/<block_id>/
        -> Lấy trạng thái Resume.

    POST /tracking/heartbeat/blocks/<block_id>/
        -> Gửi heartbeat update trạng thái.
    """
    permission_classes = [IsAuthenticated, CanViewCourseContent] 

    permission_lookup = {'block_id': ContentBlock}

    output_dto_public = BlockProgressPublicOutput
    output_dto_admin = BlockProgressAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Khởi tạo service (hoặc inject dependency nếu dùng container)
        self.interaction_service = course_tracking_service

    def get(self, request, block_id, *args, **kwargs):
        """
        Lấy trạng thái của user tại block_id được gửi lên.
        Client dùng dữ liệu này để 'seek' video tới đúng giây user đã dừng lại.
        """
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
            return Response({"detail": f"Lỗi máy chủ khi lấy tiến độ - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, block_id, *args, **kwargs):
        """
        Payload mẫu:
        {
            "interaction_data": {
                "video_timestamp": 145.5,
                "playback_rate": 1.5
            }
        }
        block_id: Lấy từ URL
        request.data: Lấy từ Body (chỉ chứa interaction_data, time_spent_add)
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
                block_id=block_id,
                data=dto.model_dump()
            )
            
            # Return 200 OK rỗng để tiết kiệm băng thông (Heartbeat cần nhẹ)
            return Response({
                "status": "synced", 
                "is_completed": user_block_progress_domain.is_completed,
                "progress": user_block_progress_domain.progress_percentage,
            }, status=status.HTTP_200_OK)
        
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
            return Response({"detail": f"Lỗi máy chủ khi đồng bộ tiến độ - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# RESUME COURSE
# ==========================================
class CourseResumeView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /courses/<course_id>/resume/
    Tìm bài học để user tiếp tục học.
    """
    permission_classes = [IsAuthenticated, CanViewCourseContent]
    
    # AutoPermissionCheckMixin sẽ dùng cái này để check quyền truy cập Course
    permission_lookup = {'course_id': Course} 

    # Reuse Serializer của Heartbeat vì cấu trúc output giống hệt nhau
    output_dto_public = BlockProgressPublicOutput 
    output_dto_admin = BlockProgressAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interaction_service = course_tracking_service # Inject service module

    def get(self, request, course_id, *args, **kwargs):
        try:
            # Gọi Service trả về Domain
            resume_domain = course_tracking_service.get_resume_state(
                user=request.user,
                course_id=course_id
            )
            return Response({"instance": resume_domain}, status=status.HTTP_200_OK)

        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
        except ValueError as e:
            # Case: Khóa học rỗng, không có bài nào
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Lỗi Resume Course: {e}", exc_info=True)
            return Response({"detail": f"Lỗi máy chủ - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# API 2: RESET PROGRESS
# ==========================================
class EnrollmentResetView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    POST /enrollments/<enrollment_id>/reset/
    Học lại từ đầu (Xóa toàn bộ tiến độ).
    """
    permission_classes = [IsAuthenticated]
    
    # Check quyền trên Enrollment
    permission_lookup = {'enrollment_id': Enrollment}
    
    output_dto_public = ResetProgressOutput
    output_dto_admin = ResetProgressOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interaction_service = course_tracking_service

    def post(self, request, enrollment_id, *args, **kwargs):
        try:
            # Gọi Service trả về Domain Result
            result_domain = course_tracking_service.reset_course_progress(
                user=request.user,
                enrollment_id=enrollment_id
            )
            
            # Trả về format chuẩn
            return Response({"instance": result_domain}, status=status.HTTP_200_OK)

        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Lỗi Reset Progress: {e}", exc_info=True)
            return Response({"detail": "Lỗi máy chủ khi reset khóa học."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CourseProgressView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /courses/<course_id>/progress/
    Output: CourseProgressPublicOutput (Chỉ thông tin khóa học)
    """
    permission_classes = [IsAuthenticated, CanViewCourseContent]
    permission_lookup = {'course_id': Course}

    # Dùng DTO riêng của Course
    output_dto_public = CourseProgressPublicOutput
    output_dto_admin = CourseProgressPublicOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interaction_service = course_tracking_service 

    def get(self, request, course_id, *args, **kwargs):
        try:
            # Service trả về CourseProgressDomain
            progress_domain = self.interaction_service.get_course_progress(
                user=request.user,
                course_id=course_id
            )
            return Response({"instance": progress_domain}, status=status.HTTP_200_OK)

        except PermissionError as e:
            # Service raise PermissionError khi user chưa enroll
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except ValueError as e:
            # Service raise ValueError khi course_id sai format
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Lỗi không mong muốn (DB sập, code bug...)
            logger.error(f"Lỗi lấy Course Progress: {e}", exc_info=True)
            return Response(
                {"detail": f"Lỗi máy chủ khi lấy tiến độ khóa học - {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    