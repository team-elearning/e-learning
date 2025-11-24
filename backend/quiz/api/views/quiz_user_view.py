# views/student_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied

from core.api.mixins import RoleBasedOutputMixin
from quiz.models import UserAnswer, Question, QuizAttempt, Quiz
from quiz.services import quiz_user_service
from quiz.serializers import QuestionTakingSerializer, QuizAttemptStartSerializer, SaveAnswerSerializer
from quiz.api.dtos.quiz_user_dto import QuizPreflightOutput, StartAttemptOutput, QuizAttemptStartInput, AttemptTakingOutput, SaveAnswerInput, SaveAnswerOutput, SubmitOutput, AttemptResultOutput, QuizItemOutput



class QuizInfoView(RoleBasedOutputMixin, APIView): 
    permission_classes = [IsAuthenticated]

    output_dto_public = QuizPreflightOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_user_service

    def get(self, request, pk): # GET: Lấy thông tin bài thi + trạng thái (đã làm bao nhiêu lần, có được thi tiếp không)
        """
        ENDPOINT: /quizzes/<id>/info/
        View chỉ gọi Service lấy data và trả về.
        """
        try:
            domain_data = quiz_user_service.get_preflight_info(pk, request.user)
            return Response({"instance": domain_data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Có thể handle NotFound riêng nếu muốn
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


class QuizAttemptStartView(RoleBasedOutputMixin, APIView): 
    permission_classes = [IsAuthenticated]

    output_dto_public = StartAttemptOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_user_service

    def post(self, request, pk): # POST: Tạo lượt làm bài mới hoặc trả về lượt đang dang dở
        """
        ENDPOINT: /quizzes/<id>/attempt/
        Nhiệm vụ:
        - Tạo QuizAttempt mới (nếu đủ điều kiện).
        - HOẶC trả về QuizAttempt cũ (nếu Resume).
        """
        try:
            serializer = QuizAttemptStartSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            input_dto = QuizAttemptStartInput(**serializer.validated_data)
        
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Service này đã bao gồm logic:
            # 1. Tìm 'in_progress' -> Nếu thấy -> return (attempt, 'resumed')
            # 2. Nếu không -> Check time/max_attempts -> Create -> return (attempt, 'created')
            result_domain = quiz_user_service.start_or_resume_attempt(pk, request.user, input_dto)
            
            response_data = {
                "attempt_id": result_domain.attempt.id,
                "action": result_domain.action,
                "detail": result_domain.detail
            }

            return Response({"instance": response_data}, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            # Lỗi logic nghiệp vụ (Hết giờ, hết lượt...)
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"detail": f"Lỗi hệ thống - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttemptDetailView(RoleBasedOutputMixin, APIView):
    """
    GET /attempts/<id>/
    Màn hình làm bài thi (Test Taking Interface).
    """
    permission_classes = [IsAuthenticated]
    
    # Định nghĩa Output DTO
    output_dto_public = AttemptTakingOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_user_service

    # GET: Lấy chi tiết đề thi (câu hỏi, thời gian còn lại, các câu trả lời đã lưu)
    def get(self, request, pk):
        try:
            # 1. Gọi Service lấy Context Domain
            taking_context = self.quiz_service.get_attempt_taking_context(pk, request.user)
            
            # 2. Trả về Response (Mixin sẽ tự map sang AttemptTakingOutput JSON)
            return Response({"instance": taking_context}, status=status.HTTP_200_OK)
            
        except PermissionDenied as e:
            # Nếu bài thi đã nộp, trả về 403 hoặc mã lỗi riêng để FE redirect
            return Response({"detail": str(e), "code": "ATTEMPT_COMPLETED"}, status=status.HTTP_403_FORBIDDEN)
            
        except Exception as e:
            return Response({"detail": f"Lỗi tải đề thi: {str(e)}"}, status=status.HTTP_404_NOT_FOUND)


class AttemptSaveAnswerView(RoleBasedOutputMixin, APIView): # POST: Lưu câu trả lời (Auto-save) & Đánh dấu (Flag)
    """
    POST /attempts/<id>/save/
    Nhiệm vụ: Auto-save đáp án & Đánh dấu (Flag).
    """
    permission_classes = [IsAuthenticated]
    
    # Định nghĩa Output DTO cho Mixin
    output_dto_public = SaveAnswerOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_user_service

    def post(self, request, pk):
        # 1. Serializer (Validate JSON format)
        serializer = SaveAnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Input DTO
        try:
            input_dto = SaveAnswerInput(**serializer.validated_data)
    
            # 3. Service & Domain Logic
            # Service trả về SaveAnswerOutput (Pydantic object)
            result_domain = self.quiz_service.save_answer(pk, request.user, input_dto.to_dict())
            
            # 4. Response (Mixin sẽ tự xử lý Pydantic -> JSON)
            # Trả về instance để Mixin map vào output_dto_public
            return Response({"instance": result_domain}, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            # Lỗi nghiệp vụ (ví dụ: Hết giờ mà vẫn cố save)
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
        except Exception as e:
            return Response({"detail": f"Lỗi hệ thống: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttemptSubmitView(RoleBasedOutputMixin, APIView):
    """
    POST /attempts/<id>/submit/
    Nhiệm vụ: 
    - Chốt bài thi (Kết thúc thời gian làm bài).
    - Tính điểm (Grading) ngay lập tức hoặc queue job chấm.
    """
    permission_classes = [IsAuthenticated]
    output_dto_public = SubmitOutput # DTO trả về điểm sơ bộ hoặc thông báo thành công

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_user_service

    def post(self, request, pk): # POST: NỘP BÀI (SUBMIT)
        try:
            # Gọi service để đổi state -> completed, tính điểm
            result_domain = self.quiz_service.submit_attempt(pk, request.user)
            
            return Response({"instance": result_domain}, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttemptResultView(RoleBasedOutputMixin, APIView):
    """
    GET /attempts/<id>/result/
    Nhiệm vụ: Hiển thị kết quả sau khi nộp.
    Logic hiển thị (Exam vs Practice) nên nằm trong Service để trả về DTO phù hợp.
    """
    permission_classes = [IsAuthenticated]
    output_dto_public = AttemptResultOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_user_service

    def get(self, request, pk): # GET: XEM KẾT QUẢ (RESULT)
        try:
            # Service cần check: 
            # 1. User có phải chủ attempt không?
            # 2. Attempt đã state='completed' chưa?
            # 3. Quiz config: show_score=True? show_correct_answer=True?
            result_context = self.quiz_service.get_attempt_result(pk, request.user)
            
            return Response({"instance": result_context}, status=status.HTTP_200_OK)
            
        except PermissionDenied as e:
            return Response({"detail": "Bạn không có quyền xem kết quả này."}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        

class QuizListView(RoleBasedOutputMixin, APIView):
    """
    GET /
    Query Params:
        ?mode=exam      -> Lấy bài kiểm tra
        ?mode=practice  -> Lấy bài luyện tập
    """
    permission_classes = [IsAuthenticated]
    output_dto_public = QuizItemOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_user_service # Instance service của bạn

    def get(self, request):
        mode_param = request.query_params.get('mode', None) # exam | practice
        
        try:
            # 1. Gọi Service
            domain_list = self.quiz_service.get_quiz_list(request.user, mode_filter=mode_param)
            
            # Nếu dùng RoleBasedOutputMixin chuẩn, bạn có thể trả về dict:
            return Response({"instance": domain_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": f"Lỗi lấy danh sách: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        