import logging
import uuid
import magic
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework import permissions
from media.models import UploadedFile
from django.utils import timezone
from datetime import timedelta
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden, FileResponse, Http404

from content.models import Course
from media.models import UploadedFile, FileStatus
from media.serializers import FileUploadInputSerializer, FileUpdateInputSerializer
from custom_account.api.mixins import RoleBasedOutputMixin
from custom_account.services.exceptions import DomainError, UserNotFoundError
from media.api.dtos.file_dto import FileInputDTO, FileOutputDTO, FileUpdateInputDTO
from media.services import file_service



class FileUploadView(RoleBasedOutputMixin, APIView):
    # Yêu cầu user đã đăng nhập
    permission_classes = [permissions.IsAuthenticated]
    
    # Cần parser cho file upload
    parser_classes = [MultiPartParser, FormParser]

    # --- Chỉ định Pydantic Output DTOs cho Mixin ---
    output_dto_public = FileOutputDTO
    output_dto_admin = FileOutputDTO # (Hoặc một DTO admin chi tiết hơn nếu bạn có)

    def post(self, request, *args, **kwargs):
        
        # BƯỚC 1: Validate bằng DRF Serializer
        serializer = FileUploadInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # BƯỚC 2: Chuyển vào Pydantic Input DTO (như bạn yêu cầu)
        try:
            file_input_dto = FileInputDTO(**serializer.validated_data)
        except Exception as e:
            return Response(
                {"error": f"Lỗi tạo DTO: {e}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # BƯỚC 3: Gọi Service
            # Service nhận user_id (từ context) và dict (từ DTO)
            file_domain = file_service.create_file_upload(
                user_id=request.user.id,
                data=file_input_dto.to_dict() 
            )

            # BƯỚC 4: Trả về 'instance' cho Mixin
            # Mixin của bạn sẽ bắt "instance", thấy nó là Django model,
            # dùng FileOutputDTO (với from_attributes=True) để
            # đọc 'id', 'status' và property 'url' rồi serialize.
            return Response(
                {"instance": file_domain}, 
                status=status.HTTP_201_CREATED
            )

        except (DomainError, UserNotFoundError) as e:
            # Bắt lỗi nghiệp vụ từ Service
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Lỗi upload file không xác định: {e}", exc_info=True)
            return Response(
                {"error": "Đã xảy ra lỗi hệ thống."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PublicDownloadFileView(APIView):
    """
    View này "gác cổng" tất cả các file đã commit.
    """
    permission_classes = [IsAuthenticated] # Yêu cầu user phải đăng nhập

    def get(self, request, file_id):
        # 1. Lấy bản ghi UploadedFile bằng ID
        # Chỉ lấy file đã commit, chưa bao giờ trả về file 'staging'
        file_obj = get_object_or_404(
            UploadedFile, 
            id=file_id, 
            status=FileStatus.COMMITTED
        )

        # 2. KIỂM TRA QUYỀN (Bước quan trọng nhất)
        if not file_service.user_has_access_to_file(request.user, file_obj):
            # Nếu không có quyền, trả về lỗi 403 Forbidden
            return HttpResponseForbidden("Bạn không có quyền truy cập file này.")

        # 3. TRẢ FILE VỀ (Nếu đã có quyền)
        try:
            # Dòng này OK
            file_handle = file_obj.file.open('rb')

            # --- SỬA LỖI BẰNG PYTHON-MAGIC ---
            
            # 1. Đọc một vài byte đầu tiên của file
            #    (đủ để "nếm" file mà không cần đọc hết file lớn)
            file_buffer = file_handle.read(2048) # Đọc 2KB đầu tiên
            
            # 2. Rất quan trọng: Quay lại đầu file
            #    để FileResponse có thể đọc lại từ đầu để gửi đi
            file_handle.seek(0) 

            # 3. Dùng magic để "sniff" (nếm) buffer
            #    mime=True sẽ trả về chuỗi MIME (ví dụ: 'image/jpeg')
            content_type = magic.from_buffer(file_buffer, mime=True)
            
            # --- HẾT PHẦN SỬA ---

            # Dùng content_type vừa "nếm" được
            response = FileResponse(
                file_handle, 
                content_type=content_type # (Ví dụ: 'image/jpeg')
            )
            
            # (Tùy chọn) Thêm tên file gốc để trình duyệt hiển thị
            # response['Content-Disposition'] = f'inline; filename="{file_obj.original_filename}"'
            
            return response
            
        except FileNotFoundError:
            raise Http404("Không tìm thấy file trên server.")
        except Exception as e:
            # In lỗi ra để debug
            print(f"LỖI THỰC TẾ KHI MỞ FILE {file_obj.id}: {repr(e)}")
            return Response({"detail": "Lỗi khi đọc file."}, status=500)
        

# --------------------------------------- ADMIN ----------------------------------------
logger = logging.getLogger(__name__)

class CleanupStagingFilesView(APIView):
    """
    API View (Admin-only) để dọn dẹp các file "staging" mồ côi.
    Chấp nhận POST với JSON: {"days_old": x} (mặc định là 1)
    """
    
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        
        try:
            # 1. Xác thực Input (Logic này thuộc về View)
            days_to_clean = int(request.data.get('days_old', 1))
            if days_to_clean <= 0:
                raise ValueError() # Sẽ bị bắt ở dưới
                
        except (ValueError, TypeError):
            return Response(
                {"error": "Trường 'days_old' không hợp lệ. Phải là một số nguyên dương."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            logger.info(f"Admin user '{request.user}' yêu cầu dọn dẹp TOÀN BỘ file...")

            # --- TÁC VỤ 1: Dọn 'staging' (Nhanh) ---
            logger.info(f"Bắt đầu dọn dẹp file staging (cũ hơn {days_to_clean} ngày)...")
            staging_result = file_service.cleanup_staging_files(days_old=days_to_clean)
            staging_count = staging_result.get("deleted_count", 0)
            logger.info(f"Dọn 'staging' xong. Đã xóa {staging_count} file.")


            # --- TÁC VỤ 2: Dọn 'file hỏng' (Rất chậm) ---
            logger.warning(f"Bắt đầu quét file hỏng (tác vụ chậm)...")
            broken_result = file_service.cleanup_broken_links()
            broken_count = broken_result.get("deleted_count", 0)
            logger.warning(f"Quét 'file hỏng' xong. Đã xóa {broken_count} file.")


            # 3. Trả về Response (Gộp kết quả)
            total_deleted = staging_count + broken_count
            
            return Response(
                {
                    "message": f"Dọn dẹp hoàn tất!",
                    "files_deleted_staging": staging_count,
                    "files_deleted_broken_links": broken_count,
                    "total_files_deleted": total_deleted,
                    "warning": "Đây là API chỉ để test. Không sử dụng trong production do nguy cơ timeout."
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            # Bắt các lỗi chung từ service (ví dụ: mất kết nối CSDL, S3)
            logger.error(f"Lỗi xảy ra trong quá trình dọn dẹp file: {e}", exc_info=True)
            return Response(
                {"error": f"Đã xảy ra lỗi hệ thống trong quá trình dọn dẹp: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
    output_dto_admin = FileOutputDTO
    output_dto_public = FileOutputDTO # (Dù public sẽ không bao giờ vào được)

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
                {"error": "Đã xảy ra lỗi hệ thống khi tải danh sách file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class FileDetailView(RoleBasedOutputMixin, APIView):
    """
    API View (Admin-only) để GET (Detail), PATCH, và DELETE một file.
    """
    
    permission_classes = [permissions.IsAdminUser]
    
    # --- Chỉ định Pydantic Output DTOs cho Mixin ---
    output_dto_admin = FileOutputDTO
    output_dto_public = FileOutputDTO

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
            file_input_dto = FileUpdateInputDTO(**serializer.validated_data)
            
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
            return Response({"error": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
