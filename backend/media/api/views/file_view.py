import logging
import uuid
import threading
from django.http import Http404, HttpResponseRedirect
from django.core.cache import cache 
from django.core.exceptions import PermissionDenied
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.mixins import RoleBasedOutputMixin
from core.exceptions import DomainError, UserNotFoundError, AccessDeniedError
from media.serializers import FileUploadInitSerializer, FileUpdateInputSerializer
from media.api.dtos.file_dto import FileInitInput, FileInitOutput, FileOutput, FileUpdateInput
from media.services import file_service
from media.models import UploadedFile, FileStatus



class FileUploadInitView(RoleBasedOutputMixin, APIView):
    parser_classes = [JSONParser] 
    permission_classes = [IsAuthenticated]

    output_dto_public = FileInitOutput
    output_dto_admin = FileInitOutput

    def post(self, request):
        serializer = FileUploadInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            input_dto = FileInitInput(**serializer.validated_data)

            domain_obj = file_service.initiate_file_upload(request.user, input_dto.to_dict())
            return Response({"instance": domain_obj}, status=status.HTTP_201_CREATED) # Trả về URL cho frontend
        
        except DomainError as e:
            return Response({"error": str(e)}, status=400)
        

class FileUploadConfirmView(RoleBasedOutputMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    output_dto_public = FileOutput
    output_dto_admin = FileOutput

    def post(self, request, file_id):
        try:
            # Gọi Service
            file_domain = file_service.confirm_file_upload(
                user=request.user, 
                file_id=file_id
            )
            
            # Return instance để Mixin tự xử lý Output DTO
            return Response(
                {"instance": file_domain}, 
                status=status.HTTP_200_OK
            )

        except (DomainError, UploadedFile.DoesNotExist) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)


class PublicDownloadFileView(APIView):
    """
    View này "gác cổng" tất cả các file đã commit.
    """
    permission_classes = [IsAuthenticated] # Yêu cầu user phải đăng nhập

    # 2. QUAN TRỌNG: Khai báo renderer này để DRF không bọc HTML/JSON vào file
    renderer_classes = [JSONRenderer]

    def get(self, request, file_id):
        try:
            s3_url = file_service.serve_file(request, file_id, request.user)
            return HttpResponseRedirect(s3_url)

        except ValidationError as e:
            # Lỗi ID không đúng định dạng UUID
            return Response(
                {"error": "BAD_REQUEST", "detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        except PermissionDenied as e:
            # Service raise PermissionDenied -> Trả về 403
            return Response(
                {"error": "FORBIDDEN", "detail": str(e)}, 
                status=status.HTTP_403_FORBIDDEN
            )

        except (FileNotFoundError, Http404) as e:
            # Service raise ObjectDoesNotExist -> Trả về 404
            return Response(
                {"error": "NOT_FOUND", "detail": f"File không tồn tại hoặc đã bị xóa - {str(e)}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        except OSError as e:
            # Lỗi kết nối AWS S3 (được Service map từ Exception gốc)
            return Response(
                {"error": "SERVICE_UNAVAILABLE", "detail": f"Hệ thống file tạm thời gián đoạn - {str(e)}"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except Exception as e:
            # Các lỗi không xác định (Code lởm, logic sai...)
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "INTERNAL_SERVER_ERROR", "detail": f"Lỗi hệ thống không xác định - {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

# --------------------------------------- ADMIN ----------------------------------------
logger = logging.getLogger(__name__)

class CleanupStagingFilesView(APIView):
    """
    API kích hoạt dọn dẹp file rác.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        days_old = request.data.get('days_old', 1)

        # 1. Gọi Service
        task_domain = file_service.trigger_background_cleanup(days_old=days_old)

        # 2. Map Domain sang HTTP Response
        if not task_domain.is_started:
            # Trường hợp bị Lock -> Trả về 429 Too Many Requests
            return Response(
                {"error": task_domain.message},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Trường hợp chạy thành công -> Trả về 202 Accepted
        return Response(
            {
                "message": task_domain.message,
                "note": "Kiểm tra log server để xem chi tiết tiến độ."
            },
            status=status.HTTP_202_ACCEPTED
        )
        

class ListAllFilesView(RoleBasedOutputMixin, APIView):
    """
    API View (Admin-only) để xem TẤT CẢ các file media đã upload.
    Chỉ chấp nhận phương thức GET.
    """
    
    # Yêu cầu user phải là Admin
    permission_classes = [permissions.IsAdminUser]
    
    # --- Chỉ định Pydantic Output DTOs cho Mixin ---
    # Mixin sẽ dùng DTO này để serialize output
    output_dto_admin = FileOutput
    output_dto_public = FileOutput # (Dù public sẽ không bao giờ vào được)

    def get(self, request, *args, **kwargs):
        """
        Xử lý request GET, trả về danh sách tất cả file.
        """
        try:
            logger.info(f"Admin user '{request.user}' yêu cầu danh sách tất cả file.")
            
            # 1. Gọi Service
            # Service trả về một QuerySet (hiệu quả nhất)
            all_files_queryset = file_service.list_all_files()
            
            # 2. Trả về 'instance' cho Mixin
            # Mixin của bạn sẽ thấy 'instance' là một QuerySet
            # và tự động áp dụng 'FileOutputDTO' với 'many=True'
            return Response(
                {"instance": all_files_queryset}, 
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách file: {e}", exc_info=True)
            return Response(
                {"error": f"Đã xảy ra lỗi hệ thống khi tải danh sách file - {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class FileDetailView(RoleBasedOutputMixin, APIView):
    """
    API View (Admin-only) để GET (Detail), PATCH, và DELETE một file.
    """
    
    permission_classes = [permissions.IsAdminUser]
    
    # --- Chỉ định Pydantic Output DTOs cho Mixin ---
    output_dto_admin = FileOutput
    output_dto_public = FileOutput

    def get(self, request, file_id: uuid.UUID, *args, **kwargs):
        """
        Xử lý GET: Lấy chi tiết 1 file.
        """
        try:
            logger.info(f"Admin user '{request.user}' yêu cầu xem file ID {file_id}.")
            
            # 1. Gọi Service
            file_domain = file_service.get_file_by_id(file_id=file_id)
            
            # 2. Trả về 'instance' cho Mixin
            return Response(
                {"instance": file_domain}, 
                status=status.HTTP_200_OK
            )
        
        except FileNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Lỗi khi GET file {file_id}: {e}", exc_info=True)
            return Response({"error": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, file_id: uuid.UUID, *args, **kwargs):
        """
        Xử lý PATCH: Cập nhật một phần file (ví dụ: status, component).
        """
        logger.info(f"Admin user '{request.user}' yêu cầu PATCH file ID {file_id}.")
        
        # BƯỚC 1: Validate bằng DRF Serializer (partial=True cho PATCH)
        serializer = FileUpdateInputSerializer(data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)

        # BƯỚC 2: Chuyển vào Pydantic Input DTO
        try:
            file_input_dto = FileUpdateInput(**serializer.validated_data)
            
            # Dùng .model_dump() để chỉ lấy các trường đã được gửi
            # (Rất quan trọng cho PATCH)
            data_to_update = file_input_dto.model_dump(exclude_unset=True)
            
            if not data_to_update:
                return Response(
                    {"error": "Không có trường hợp lệ nào được gửi để cập nhật."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response({"error": f"Lỗi tạo DTO: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # BƯỚC 3: Gọi Service
        try:
            updated_file_domain = file_service.update_file(
                file_id=file_id,
                data=data_to_update
            )
            
            # BƯỚC 4: Trả về 'instance' đã cập nhật
            return Response(
                {"instance": updated_file_domain}, 
                status=status.HTTP_200_OK
            )
        
        except FileNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except DomainError as e: # (Ví dụ: validate nghiệp vụ trong service)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi khi PATCH file {file_id}: {e}", exc_info=True)
            return Response({"error": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, file_id: uuid.UUID, *args, **kwargs):
        """
        Xử lý DELETE: Xóa 1 file.
        """
        logger.info(f"Admin user '{request.user}' yêu cầu XÓA file ID {file_id}.")
        
        try:
            # 1. Gọi Service
            file_service.delete_file(file_id=file_id)
            
            # 2. Trả về 200 OK với thông báo (thay vì 204)
            return Response(
                {"message": f"Đã xóa thành công file ID: {file_id}"},
                status=status.HTTP_200_OK
            )
        
        except FileNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Lỗi khi DELETE file {file_id}: {e}", exc_info=True)
            return Response({"error": f"Lỗi hệ thống - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
