import logging
import uuid
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin
from core.api.permissions import CanViewCourseContent, IsAttemptOwner
from core.exceptions import DomainError
from quiz.models import Quiz
from progress.services import quiz_attempt_service, question_attempt_service
from progress.serializers import StartQuizInputSerializer
from progress.api.dtos.quiz_attempt_dto import QuizAttemptInfoOutput, QuizAttemptResultOutput
from progress.models import QuizAttempt



logger = logging.getLogger(__name__)

class QuizAttemptInitView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET quizzes/<quiz_id>/attempt/?course_id=uuid-cua-khoa-hoc
    Chức năng: Bắt đầu làm bài hoặc Resume bài cũ. 
    Trả về ID bài làm và danh sách ID câu hỏi (để client tự loop gọi content)
    """
    permission_classes = [permissions.IsAuthenticated, CanViewCourseContent] # Học viên chỉ cần login

    permission_lookup = {'quiz_id': Quiz}

    output_dto_admin = QuizAttemptInfoOutput
    output_dto_public = QuizAttemptInfoOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = quiz_attempt_service

    def get(self, request, quiz_id: uuid.UUID, *args, **kwargs):
        """ Xem màn hình chờ (Info) """
        try:
            course_id_str = request.query_params.get('course_id')
            course_id = uuid.UUID(course_id_str) if course_id_str else None
            
            # 1. Gọi Service lấy Domain Data
            attempt_domain = self.service.start_or_resume_attempt(
                quiz_id=quiz_id, 
                user=request.user,
                course_id=course_id
            )
            return Response({"instance": attempt_domain}, status=status.HTTP_200_OK)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Lỗi hệ thống - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class QuizAttemptFinishView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    POST attempts/<attempt_id>/finish/
    Chức năng: Nộp bài (Submit All) -> Chấm điểm Batch -> Trả về kết quả tổng.
    """
    permission_classes = [permissions.IsAuthenticated, IsAttemptOwner]
    
    # AutoPermissionCheckMixin check quyền sở hữu attempt
    permission_lookup = {'attempt_id': QuizAttempt}

    # Định nghĩa Output DTO để Mixin tự động map từ Domain sang JSON
    output_dto_public = QuizAttemptResultOutput
    output_dto_admin = QuizAttemptResultOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = quiz_attempt_service

    def post(self, request, attempt_id: uuid.UUID, *args, **kwargs):
        """
        Action: Nộp bài. 
        Không cần Body Request (vì nộp là nộp hết).
        """
        try:
            # 1. Gọi Service (Logic chấm điểm Batch nằm ở đây)
            # Service trả về QuizAttemptDomain (đã có full điểm số)
            result_domain = self.service.finish_quiz_attempt(
                attempt_id=attempt_id,
                user=request.user
            )

            # 2. Return Response
            # Mixin sẽ tự động lấy 'instance' (result_domain) map vào 'QuizAttemptResultOutput'
            return Response({"instance": result_domain}, status=status.HTTP_200_OK)

        except DomainError as e:
            # Lỗi nghiệp vụ (VD: Bài đã đóng, không tìm thấy...)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # Lỗi kỹ thuật (Code bug, Database down...)
            logger.error(f"Error finishing quiz attempt {attempt_id}: {e}", exc_info=True)
            return Response({"detail": f"Lỗi hệ thống khi nộp bài - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class StartQuizAttemptView(RoleBasedOutputMixin, APIView):
#     """
#     POST /quiz/start/
#     """
#     permission_classes = [IsAuthenticated]
    
#     # Config Output DTO cho Mixin tự động map
#     output_dto_public = QuizAttemptPublicOutput
#     output_dto_admin = QuizAttemptAdminOutput 

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.quiz_service = quiz_progress_service # Inject Service

#     def post(self, request, *args, **kwargs):
#         # 1. Validate Input bằng Serializer
#         input_serializer = StartQuizInputSerializer(data=request.data)
#         try:
#             input_serializer.is_valid(raise_exception=True)
#             input_dto = StartQuizInput(**input_serializer.validated_data)
#         except Exception as e:
#             return Response({"detail": f"Dữ liệu không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             service_payload = input_dto.model_dump()

#             # 2. Gọi Service -> Nhận Domain Object
#             # View không cần biết logic tính remaining_seconds nữa
#             attempt_domain = self.quiz_service.start_quiz_attempt(
#                 user=request.user, 
#                 quiz_id=service_payload['quiz_id']
#             )

#             # 3. Trả về Response
#             # Key "instance" giúp RoleBasedOutputMixin hiểu cần serialize object này
#             return Response(
#                 {"instance": attempt_domain}, 
#                 status=status.HTTP_201_CREATED
#             )

#         except ValueError as e:
#             # Lỗi nghiệp vụ (Hết lượt, chưa mở đề...)
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
#         except Exception as e:
#             logger.error(f"Lỗi Start Quiz: {e}", exc_info=True)
#             return Response({"detail": f"Lỗi hệ thống - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)