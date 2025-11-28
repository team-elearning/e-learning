import logging
import uuid
from django.http import Http404, HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.mixins import RoleBasedOutputMixin
from core.exceptions import DomainError, UserNotFoundError, AccessDeniedError
from media.serializers import FileUploadInitSerializer
from media.api.dtos.file_dto import FileInitInput, FileInitOutput, FileOutput
from media.services import file_service
from media.models import UploadedFile, FileStatus



# class FileUploadView(RoleBasedOutputMixin, APIView):
#     # Yêu cầu user đã đăng nhập
#     permission_classes = [permissions.IsAuthenticated]
    
#     # Cần parser cho file upload
#     parser_classes = [MultiPartParser, FormParser]

#     # --- Chỉ định Pydantic Output DTOs cho Mixin ---
#     output_dto_public = FileOutputDTO
#     output_dto_admin = FileOutputDTO # (Hoặc một DTO admin chi tiết hơn nếu bạn có)

#     def post(self, request, *args, **kwargs):
        
#         # BƯỚC 1: Validate bằng DRF Serializer
#         serializer = FileUploadInputSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         # BƯỚC 2: Chuyển vào Pydantic Input DTO (như bạn yêu cầu)
#         try:
#             file_input_dto = FileInputDTO(**serializer.validated_data)
#         except Exception as e:
#             return Response(
#                 {"error": f"Lỗi tạo DTO: {e}"}, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             # BƯỚC 3: Gọi Service
#             # Service nhận user_id (từ context) và dict (từ DTO)
#             file_domain = file_service.create_file_upload(
#                 user=request.user,
#                 data=file_input_dto.to_dict() 
#             )

#             # BƯỚC 4: Trả về 'instance' cho Mixin
#             # Mixin của bạn sẽ bắt "instance", thấy nó là Django model,
#             # dùng FileOutputDTO (với from_attributes=True) để
#             # đọc 'id', 'status' và property 'url' rồi serialize.
#             return Response(
#                 {"instance": file_domain}, 
#                 status=status.HTTP_201_CREATED
#             )

#         except (DomainError, UserNotFoundError) as e:
#             # Bắt lỗi nghiệp vụ từ Service
#             return Response(
#                 {"error": str(e)}, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         except Exception as e:
#             logger.error(f"Lỗi upload file không xác định: {e}", exc_info=True)
#             return Response(
#                 {"error": f"Đã xảy ra lỗi hệ thống - {str(e)}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


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


# class BinaryFileRenderer(BaseRenderer):
#     media_type = 'application/octet-stream'
#     format = 'binary'

#     def render(self, data, media_type=None, renderer_context=None):
#         # NẾU DATA LÀ TỪ ĐIỂN (LỖI) -> Trả về JSON string
#         if isinstance(data, (dict, list)):
#             return json.dumps(data).encode('utf-8')
            
#         # NẾU LÀ FILE -> Trả về nguyên gốc
#         return data
    

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
        

# class ListAllFilesView(RoleBasedOutputMixin, APIView):
#     """
#     API View (Admin-only) để xem TẤT CẢ các file media đã upload.
#     Chỉ chấp nhận phương thức GET.
#     """
    
#     # Yêu cầu user phải là Admin
#     permission_classes = [permissions.IsAdminUser]
    
#     # --- Chỉ định Pydantic Output DTOs cho Mixin ---
#     # Mixin sẽ dùng DTO này để serialize output
#     output_dto_admin = FileOutputDTO
#     output_dto_public = FileOutputDTO # (Dù public sẽ không bao giờ vào được)

#     def get(self, request, *args, **kwargs):
#         """
#         Xử lý request GET, trả về danh sách tất cả file.
#         """
#         try:
#             logger.info(f"Admin user '{request.user}' yêu cầu danh sách tất cả file.")
            
#             # 1. Gọi Service
#             # Service trả về một QuerySet (hiệu quả nhất)
#             all_files_queryset = file_service.list_all_files()
            
#             # 2. Trả về 'instance' cho Mixin
#             # Mixin của bạn sẽ thấy 'instance' là một QuerySet
#             # và tự động áp dụng 'FileOutputDTO' với 'many=True'
#             return Response(
#                 {"instance": all_files_queryset}, 
#                 status=status.HTTP_200_OK
#             )
        
#         except Exception as e:
#             logger.error(f"Lỗi khi lấy danh sách file: {e}", exc_info=True)
#             return Response(
#                 {"error": f"Đã xảy ra lỗi hệ thống khi tải danh sách file - {str(e)}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
        

# class FileDetailView(RoleBasedOutputMixin, APIView):
#     """
#     API View (Admin-only) để GET (Detail), PATCH, và DELETE một file.
#     """
    
#     permission_classes = [permissions.IsAdminUser]
    
#     # --- Chỉ định Pydantic Output DTOs cho Mixin ---
#     output_dto_admin = FileOutputDTO
#     output_dto_public = FileOutputDTO

#     def get(self, request, file_id: uuid.UUID, *args, **kwargs):
#         """
#         Xử lý GET: Lấy chi tiết 1 file.
#         """
#         try:
#             logger.info(f"Admin user '{request.user}' yêu cầu xem file ID {file_id}.")
            
#             # 1. Gọi Service
#             file_domain = file_service.get_file_by_id(file_id=file_id)
            
#             # 2. Trả về 'instance' cho Mixin
#             return Response(
#                 {"instance": file_domain}, 
#                 status=status.HTTP_200_OK
#             )
        
#         except FileNotFoundError as e:
#             return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error(f"Lỗi khi GET file {file_id}: {e}", exc_info=True)
#             return Response({"error": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def patch(self, request, file_id: uuid.UUID, *args, **kwargs):
#         """
#         Xử lý PATCH: Cập nhật một phần file (ví dụ: status, component).
#         """
#         logger.info(f"Admin user '{request.user}' yêu cầu PATCH file ID {file_id}.")
        
#         # BƯỚC 1: Validate bằng DRF Serializer (partial=True cho PATCH)
#         serializer = FileUpdateInputSerializer(data=request.data, partial=True)
#         try:
#             serializer.is_valid(raise_exception=True)
#         except ValidationError as e:
#             return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)

#         # BƯỚC 2: Chuyển vào Pydantic Input DTO
#         try:
#             file_input_dto = FileUpdateInputDTO(**serializer.validated_data)
            
#             # Dùng .model_dump() để chỉ lấy các trường đã được gửi
#             # (Rất quan trọng cho PATCH)
#             data_to_update = file_input_dto.model_dump(exclude_unset=True)
            
#             if not data_to_update:
#                 return Response(
#                     {"error": "Không có trường hợp lệ nào được gửi để cập nhật."}, 
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
                
#         except Exception as e:
#             return Response({"error": f"Lỗi tạo DTO: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#         # BƯỚC 3: Gọi Service
#         try:
#             updated_file_domain = file_service.update_file(
#                 file_id=file_id,
#                 data=data_to_update
#             )
            
#             # BƯỚC 4: Trả về 'instance' đã cập nhật
#             return Response(
#                 {"instance": updated_file_domain}, 
#                 status=status.HTTP_200_OK
#             )
        
#         except FileNotFoundError as e:
#             return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except DomainError as e: # (Ví dụ: validate nghiệp vụ trong service)
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Lỗi khi PATCH file {file_id}: {e}", exc_info=True)
#             return Response({"error": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def delete(self, request, file_id: uuid.UUID, *args, **kwargs):
#         """
#         Xử lý DELETE: Xóa 1 file.
#         """
#         logger.info(f"Admin user '{request.user}' yêu cầu XÓA file ID {file_id}.")
        
#         try:
#             # 1. Gọi Service
#             file_service.delete_file(file_id=file_id)
            
#             # 2. Trả về 200 OK với thông báo (thay vì 204)
#             return Response(
#                 {"message": f"Đã xóa thành công file ID: {file_id}"},
#                 status=status.HTTP_200_OK
#             )
        
#         except FileNotFoundError as e:
#             return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error(f"Lỗi khi DELETE file {file_id}: {e}", exc_info=True)
#             return Response({"error": "Lỗi hệ thống."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
