# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from django.core.exceptions import ValidationError as DjangoValidationError
# from pydantic import ValidationError as PydanticValidationError
# import logging

# from core.api.mixins import RoleBasedOutputMixin

# # Giả định các import từ project của bạn
# # from core.mixins import RoleBasedOutputMixin 
# # from quiz.serializers import QuizInputSerializer
# # from quiz.dtos import QuizCreateInput, QuizListOutput, QuizDetailOutput
# # from quiz.services import quiz_management_service

# logger = logging.getLogger(__name__)

# class InstructorExamListCreateView(RoleBasedOutputMixin, APIView):
#     """
#     GET /instructor/quizzes/?course_id=...
#         -> Lấy danh sách các bài Quiz trong một khóa học.
    
#     POST /instructor/quizzes/
#         -> Tạo mới một Quiz (Cấu hình sơ khởi: Tên, Chế độ, Thời gian).
#         -> Tương đương hành động 'Add New Quiz' trong Moodle.
#     """
#     permission_classes = [IsAuthenticated] # Cần thêm permission check 'IsInstructor'

#     # Cấu hình cho RoleBasedOutputMixin (nếu bạn dùng)
#     output_dto_public = QuizListOutput 
#     output_dto_admin = QuizListOutput

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Inject Service quản lý Quiz
#         self.quiz_service = quiz_management_service

#     def get(self, request, *args, **kwargs):
#         """
#         Lấy danh sách Quiz. Thường lọc theo Course ID.
#         """
#         course_id = request.query_params.get('course_id')
        
#         if not course_id:
#             return Response({"detail": "Cần cung cấp course_id."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Service sẽ lo việc filter và check xem user có phải giáo viên của course này không
#             quizzes_domain = self.quiz_service.list_quizzes_by_course(
#                 user=request.user, 
#                 course_id=course_id
#             )
#             # RoleBasedOutputMixin sẽ tự serialize danh sách này nếu bạn đã cấu hình
#             # Ở đây tôi trả về response thủ công để dễ hình dung
#             return Response({"results": quizzes_domain}, status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.error(f"Lỗi lấy danh sách Quiz: {e}", exc_info=True)
#             return Response({"detail": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def post(self, request, *args, **kwargs):
#         """
#         Tạo Quiz mới.
#         Payload mẫu (theo model của bạn):
#         {
#             "course_id": "...",
#             "title": "Bài kiểm tra giữa kỳ",
#             "mode": "exam",
#             "time_limit": "00:45:00",
#             "time_open": "2025-11-25T08:00:00Z",
#             "questions_count": 20,
#             "shuffle_questions": true
#         }
#         """
#         # 1. Validate sơ bộ bằng DRF Serializer (check kiểu dữ liệu)
#         serializer = QuizInputSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         # 2. Gọi Service xử lý nghiệp vụ
#         try:
#             # Map data sang Pydantic DTO
#             dto = QuizCreateInput(**serializer.validated_data)

#             # Service thực hiện: 
#             # - Validate logic (Time close > Time open)
#             # - Tạo record trong DB
#             new_quiz_domain = self.quiz_service.create_quiz(
#                 user=request.user, 
#                 data=dto.model_dump()
#             )
            
#             return Response({"instance": new_quiz_domain, "detail": "Tạo bài kiểm tra thành công."}, status=status.HTTP_201_CREATED)

#         except PydanticValidationError as e:
#             return Response({"detail": f"Dữ liệu không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)
#         except ValueError as e:
#             # Ví dụ: Ngày đóng nhỏ hơn ngày mở
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi tạo Quiz: {e}", exc_info=True)
#             return Response({"detail": "Lỗi server khi tạo bài kiểm tra."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# class InstructorExamDetailView(RoleBasedOutputMixin, APIView):
#     """
#     GET /instructor/quizzes/<quiz_id>/
#         -> Xem chi tiết cấu hình hiện tại.

#     PUT /instructor/quizzes/<quiz_id>/
#         -> Cập nhật cấu hình (Thời gian, Mode, Quy tắc).
#         -> Logic Moodle: Nếu đổi sang 'Practice', cần reset max_attempts về null chẳng hạn.
    
#     DELETE /instructor/quizzes/<quiz_id>/
#         -> Xóa bài quiz.
#     """
#     permission_classes = [IsAuthenticated]

#     output_dto_public = QuizDetailOutput
#     output_dto_admin = QuizDetailOutput

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.quiz_service = quiz_management_service

#     def get(self, request, quiz_id, *args, **kwargs):
#         try:
#             quiz_domain = self.quiz_service.get_quiz_detail(
#                 user=request.user, 
#                 quiz_id=quiz_id
#             )
#             return Response({"instance": quiz_domain}, status=status.HTTP_200_OK)
#         except ValueError as e: # Không tìm thấy quiz
#              return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

#     def put(self, request, quiz_id, *args, **kwargs):
#         """
#         Update settings.
#         Logic tham khảo Moodle:
#         - Nếu mode='exam': Force 'show_correct_answer' = False (trong lúc thi), time_limit != null.
#         - Nếu mode='practice': Allow 'show_correct_answer' = True, grading_method = 'highest'.
#         Việc này nên handle trong Service, View chỉ nhận data.
#         """
#         serializer = QuizInputSerializer(data=request.data, partial=True)
#         if not serializer.is_valid():
#              return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             dto = QuizUpdateConfigInput(**serializer.validated_data)

#             updated_quiz_domain = self.quiz_service.update_quiz_config(
#                 user=request.user,
#                 quiz_id=quiz_id,
#                 data=dto.model_dump(exclude_unset=True) # Chỉ update trường có gửi lên
#             )
            
#             return Response({"instance": updated_quiz_domain, "detail": "Cập nhật cấu hình thành công."}, status=status.HTTP_200_OK)

#         except ValueError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi update Quiz {quiz_id}: {e}", exc_info=True)
#             return Response({"detail": "Lỗi server."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def delete(self, request, quiz_id, *args, **kwargs):
#         """
#         Xóa bài Quiz.
#         Lưu ý: Trong Moodle, nếu đã có sinh viên làm bài (QuizAttempt tồn tại), 
#         thường sẽ chặn xóa hoặc chỉ cho xóa mềm (archive).
#         """
#         try:
#             self.quiz_service.delete_quiz(user=request.user, quiz_id=quiz_id)
#             return Response({"detail": "Đã xóa bài kiểm tra."}, status=status.HTTP_204_NO_CONTENT)
#         except ValueError as e: # Có thể là lỗi "Đã có người làm bài, không được xóa"
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi xóa Quiz {quiz_id}: {e}", exc_info=True)
#             return Response({"detail": "Lỗi server."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)