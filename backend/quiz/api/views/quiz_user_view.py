# views/student_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError

from core.api.mixins import RoleBasedOutputMixin
from quiz.models import UserAnswer, Question, QuizAttempt, Quiz
from quiz.services import quiz_user_service
from quiz.serializers import QuestionTakingSerializer
from quiz.api.dtos.quiz_user_dto import QuizPreflightOutput



class QuizInfoView(RoleBasedOutputMixin, APIView):
    permission_classes = [IsAuthenticated]

    output_dto_public = QuizPreflightOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_user_service

    def get(self, request, pk):
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


class StudentQuizAttemptStartView(RoleBasedOutputMixin, APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quiz_service = quiz_user_service

    def post(self, request, pk):
        """
        ENDPOINT: /student/quizzes/<id>/attempt/
        Nhiệm vụ:
        - Tạo QuizAttempt mới (nếu đủ điều kiện).
        - HOẶC trả về QuizAttempt cũ (nếu Resume).
        """
        
        try:
            # Service này đã bao gồm logic:
            # 1. Tìm 'in_progress' -> Nếu thấy -> return (attempt, 'resumed')
            # 2. Nếu không -> Check time/max_attempts -> Create -> return (attempt, 'created')
            attempt, action = quiz_user_service.start_or_resume_attempt(pk, request.user)
            
            return Response({
                "attempt_id": attempt.id,
                "action": action, 
                "detail": "Đã khôi phục bài làm" if action == 'resumed' else "Bắt đầu bài làm mới"
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            # Lỗi logic nghiệp vụ (Hết giờ, hết lượt...)
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"detail": f"Lỗi hệ thống - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class StudentAttemptDetailView(APIView):
#     """
#     API quan trọng nhất: Trả về toàn bộ đề thi đã được sắp xếp cho FE render.
#     LƯU Ý: KHÔNG TRẢ VỀ ĐÁP ÁN ĐÚNG (answer_payload) ở đây.
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request, pk):
#         attempt = get_object_or_404(QuizAttempt, pk=pk, user=request.user)
        
#         # 1. Lấy danh sách câu hỏi theo đúng thứ tự đã snapshot
#         question_ids = attempt.questions_order # List UUID strings
        
#         # Query set unordered
#         questions_query = Question.objects.filter(id__in=question_ids)
#         questions_dict = {str(q.id): q for q in questions_query}
        
#         # Sắp xếp lại theo questions_order
#         ordered_questions = [questions_dict[qid] for qid in question_ids if qid in questions_dict]

#         # 2. Lấy các câu trả lời đã lưu (để FE fill lại khi resume)
#         saved_answers = UserAnswer.objects.filter(attempt=attempt)
#         saved_answers_dto = {str(ans.question_id): ans.selected_options for ans in saved_answers}

#         # 3. Tính thời gian còn lại
#         time_remaining_seconds = None
#         if attempt.quiz.time_limit:
#             elapsed = (timezone.now() - attempt.time_start).total_seconds()
#             limit = attempt.quiz.time_limit.total_seconds()
#             time_remaining_seconds = max(0, limit - elapsed)

#         # Serializer thủ công hoặc dùng DRF Serializer (Khuyến nghị dùng Serializer để hide field)
#         data = {
#             "attempt_id": attempt.id,
#             "quiz_title": attempt.quiz.title,
#             "time_remaining_seconds": time_remaining_seconds,
#             "current_question_index": attempt.current_question_index,
#             "questions": QuestionTakingSerializer(ordered_questions, many=True).data, # DTO chỉ chứa đề, ko chứa đáp án
#             "saved_answers": saved_answers_dto # { "q_id": {selected: "A"} }
#         }
        
#         return Response(data)


# class StudentAttemptSaveAnswerView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         """ Auto-save 1 câu hỏi """
#         question_id = request.data.get('question_id')
#         selected_options = request.data.get('selected_options')
        
#         try:
#             save_answer(pk, question_id, selected_options, request.user)
#             return Response({"status": "saved"}, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# class StudentAttemptSubmitView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request, pk):
#         attempt = submit_attempt(pk, request.user)
#         return Response({"status": "submitted", "attempt_id": attempt.id}, status=status.HTTP_200_OK)