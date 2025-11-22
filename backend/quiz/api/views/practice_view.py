from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import ValidationError as PydanticValidationError
import logging
import uuid

from core.api.mixins import RoleBasedOutputMixin 
from core.api.permissions import IsInstructor
from quiz.services import exam_service
from quiz.serializers import PracticeInputSerializer
from quiz.api.dtos.practice_dto import PracticeCreateInput, PracticeUpdateInput, PracticePublicOutput, PracticeAdminOutput
from quiz.types import ExamFilter, ExamFetchStrategy



logger = logging.getLogger(__name__)


# ==========================================
# PUBLIC INTERFACE (INSTRUCTOR)
# ==========================================

class InstructorPracticeListView(RoleBasedOutputMixin, APIView):
    """
    API quản lý danh sách bài thi (Exam) của giáo viên.
    ENDPOINT: /instructor/practices/
    """
    permission_classes = [IsAuthenticated, IsInstructor]
    
    # DTO Output riêng cho Exam (ẩn bớt các field không cần thiết)
    output_dto_public = PracticePublicOutput
    output_dto_admin = PracticeAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exam_service = exam_service # Service chuyên biệt cho Exam

    def get(self, request, *args, **kwargs):
        """ Lấy danh sách các bài thi do giáo viên này tạo """
        try:
            practices = self.exam_service.list_quizzes(
                filters=ExamFilter(mode='practice', owner=request.user),
                strategy=ExamFetchStrategy.LIST_VIEW
            )
            return Response({"instance": practices}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": "Lỗi lấy danh sách bài thi."}, status=500)

    def post(self, request, *args, **kwargs):
        """ 
        Tạo mới bài thi.
        Service sẽ TỰ ĐỘNG set:
        - mode = 'exam'
        - grading_method = 'first' (hoặc 'last')
        - show_correct_answer = False
        """
        serializer = PracticeInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            dto = PracticeCreateInput(**serializer.validated_data)
            
            new_practice = self.exam_service.create_quiz(
                data=dto.to_dict(),
                created_by=request.user,
                mode='practice', 
                output_strategy=ExamFetchStrategy.DETAIL_VIEW
            )
            return Response({"instance": new_practice}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Lỗi hệ thống: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class InstructorPracticeDetailView(RoleBasedOutputMixin, APIView):
    """
    Chi tiết cấu hình bài thi.
    ENDPOINT: /instructor/practices/<quiz_id>/
    """
    permission_classes = [IsAuthenticated, IsInstructor]
    output_dto_public = PracticePublicOutput
    output_dto_admin = PracticeAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exam_service = exam_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        try:
            # Lấy chi tiết cấu hình (Time limit, Open/Close time...)
            exam = self.exam_service.get_quiz_single(
                filters=ExamFilter(mode='practice', owner=request.user, quiz_id=pk),
                strategy=ExamFetchStrategy.DETAIL_VIEW
            )

            return Response({"instance": exam}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Cập nhật cấu hình Exam (Không bao gồm list câu hỏi) """
        serializer = PracticeInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            dto = PracticeUpdateInput(**serializer.validated_data)
            updated_practice = self.exam_service.patch_quiz(
                quiz_id=pk,
                data=dto.to_dict(),
                actor=request.user,
                target_mode='practice', 
                output_strategy=ExamFetchStrategy.DETAIL_VIEW
            )
            return Response({"instance": updated_practice}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk: uuid.UUID, *args, **kwargs):
        try:
            self.exam_service.delete_quiz(
                quiz_id=pk, 
                actor=request.user, # Service tự check is_superuser
                target_mode='practice'
            )

            return Response(
                {"message": "Xóa bài kiểm tra thành công."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# PUBLIC INTERFACE (ADMIN)
# ==========================================

class AdminPracticeListView(RoleBasedOutputMixin, APIView):
    """
    API quản lý danh sách bài thi (Exam) của giáo viên.
    ENDPOINT: /admin/exams/
    """
    permission_classes = [IsAuthenticated, IsInstructor]
    
    # DTO Output riêng cho Exam (ẩn bớt các field không cần thiết)
    output_dto_public = PracticePublicOutput 
    output_dto_admin = PracticeAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exam_service = exam_service # Service chuyên biệt cho Exam

    def get(self, request, *args, **kwargs):
        """ Lấy danh sách các bài thi do giáo viên này tạo """
        try:
            practices = self.exam_service.list_quizzes(
                filters=ExamFilter(mode='practice'),
                strategy=ExamFetchStrategy.LIST_VIEW
            )
            return Response({"instance": practices}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": "Lỗi lấy danh sách bài thi."}, status=500)

    def post(self, request, *args, **kwargs):
        """ 
        Tạo mới bài thi.
        Service sẽ TỰ ĐỘNG set:
        - mode = 'exam'
        - grading_method = 'first' (hoặc 'last')
        - show_correct_answer = False
        """
        serializer = PracticeInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            dto = PracticeCreateInput(**serializer.validated_data)
            
            new_practice = self.exam_service.create_quiz(
                data=dto.to_dict(),
                created_by=request.user,
                mode='practice', 
                output_strategy=ExamFetchStrategy.DETAIL_VIEW
            )
            return Response({"instance": new_practice}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Lỗi hệ thống: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class AdminPracticeDetailView(RoleBasedOutputMixin, APIView):
    """
    Chi tiết cấu hình bài thi.
    ENDPOINT: /admin/exams/<quiz_id>/
    """
    permission_classes = [IsAuthenticated, IsInstructor]
    output_dto_public = PracticePublicOutput
    output_dto_admin = PracticeAdminOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exam_service = exam_service

    def get(self, request, pk: uuid.UUID, *args, **kwargs):
        try:
            # Lấy chi tiết cấu hình (Time limit, Open/Close time...)
            practice = self.exam_service.get_quiz_single(
                filters=ExamFilter(mode='practice', quiz_id=pk),
                strategy=ExamFetchStrategy.DETAIL_VIEW
            )

            return Response({"instance": practice}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk: uuid.UUID, *args, **kwargs):
        """ Cập nhật cấu hình Exam (Không bao gồm list câu hỏi) """
        serializer = PracticeInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            dto = PracticeUpdateInput(**serializer.validated_data)
            updated_practice = self.exam_service.patch_quiz(
                quiz_id=pk,
                data=dto.to_dict(),
                actor=request.user,
                target_mode='practice', 
                output_strategy=ExamFetchStrategy.DETAIL_VIEW
            )
            return Response({"instance": updated_practice}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk: uuid.UUID, *args, **kwargs):
        try:
            self.exam_service.delete_quiz(
                quiz_id=pk, 
                actor=request.user, # Service tự check is_superuser
                target_mode='practice'
            )

            return Response(
                {"message": "Xóa bài kiểm tra thành công."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)