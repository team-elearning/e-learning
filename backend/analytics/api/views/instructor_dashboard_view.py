import logging
from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from pydantic import ValidationError as PydanticValidationError

from analytics.services import course_analyze_service, course_dashboard_service
from core.api.permissions import IsInstructor
from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin, PaginationMixin
from content.models import Course
from analytics.serializers import CourseHealthAnalyzeSerializer
from analytics.api.dtos.analytics_dto import CourseHealthOverviewOutput, CourseTrendOutput, StudentRiskInfoOutput, InstructorOverviewOutput, CourseHealthAnalyzeInput
from analytics.services import instructor_overall_dashboard_service
from analytics.domains.student_risk_info_domain import StudentRiskInfoDomain
from analytics.domains.instructor_overview_domain import InstructorOverviewDomain
from analytics.tasks import async_analyze_course



logger = logging.getLogger(__name__)

class InstructorCourseHealthAnalyzeView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    POST /instructor/courses/<course_id>/analyze/
    Endpoint để Instructor kích hoạt phân tích rủi ro thủ công (On-demand).
    """
    permission_classes = [IsInstructor] 
    
    # AutoPermissionCheckMixin sẽ tự động check:
    # 1. course_id trong URL có tồn tại không?
    # 2. request.user có phải owner của course này không?
    permission_lookup = {'course_id': Course} 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics_service = course_analyze_service

    def post(self, request, course_id, *args, **kwargs):
        """
        Trigger phân tích sức khỏe lớp học.
        Flow: Serializer -> Input DTO -> Service -> Domain -> Output DTO
        """
        
        # 1. Serializer: Validate Body Request
        serializer = CourseHealthAnalyzeSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
        except DRFValidationError:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Input DTO: Convert dữ liệu sạch sang DTO
        try:
            input_dto = CourseHealthAnalyzeInput(**validated_data)
        except PydanticValidationError as e:
            return Response({"detail": f"Dữ liệu input không hợp lệ: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Service Call: Truyền tham số vào Service
        try:
            async_analyze_course.delay(str(course_id))
            
            # Lưu ý: Nếu service chạy Async (Celery), result_domain có thể chỉ là thông báo "Task Started"
            # Nếu chạy Sync (như code mẫu trước), nó là kết quả thật.
            return Response(
                {
                    "detail": "Yêu cầu phân tích đã được tiếp nhận và đang chạy ngầm.",
                    "status": "processing"
                }, 
                status=status.HTTP_202_ACCEPTED
            )

        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Lỗi trong CourseHealthAnalyzeView (POST): {e}", exc_info=True)
            return Response({"detail": f"Lỗi máy chủ khi phân tích - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class InstructorOverviewView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /instructor/overview/
    Endpoint lấy dữ liệu tổng quan Dashboard cho Giảng viên.
    """
    permission_classes = [IsAuthenticated, IsInstructor]

    output_dto_public = InstructorOverviewOutput
    output_dto_instructor = InstructorOverviewOutput
    output_dto_admin = InstructorOverviewOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics_service = instructor_overall_dashboard_service

    def get(self, request, *args, **kwargs):
        """
        Lấy thống kê tổng quan (Dashboard).
        Flow: Service -> Domain -> Output DTO/Dict -> Response
        """
        try:
            # 1. Input: Xác định Instructor ID từ User đang đăng nhập
            # Không lấy từ URL để tránh việc user A xem trộm data của user B
            instructor_id = str(request.user.id)

            # 2. Service Call: Gọi logic nghiệp vụ
            # Hàm này trả về InstructorOverviewDomain (Pydantic Model)
            domain_result = self.analytics_service.get_instructor_overview(instructor_id)

            # 4. Return Response
            # RoleBasedOutputMixin sẽ can thiệp vào đây (nếu có logic finalize_response)
            return Response({"instance": domain_result}, status=status.HTTP_200_OK)
        
        except ValueError as e:
            # Lỗi logic nghiệp vụ (ví dụ: ID không hợp lệ, User chưa kích hoạt...)
            logger.warning(f"Business Error in InstructorOverviewView: {e}")
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            # Lỗi kỹ thuật không mong muốn (DB connection, Code bug...)
            logger.error(f"System Error in InstructorOverviewView: {e}", exc_info=True)
            return Response(
                {"detail": f"Lỗi hệ thống khi tải dashboard - {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class InstructorCourseHealthOverviewView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /api/courses/<course_id>/overview/
    Lấy số liệu sức khỏe tổng quan của khóa học (Dashboard Cards).
    """
    # 1. Permission & Security
    permission_classes = [IsInstructor] # Chỉ Instructor mới được xem
    
    # Tự động check: Course có tồn tại ko? User hiện tại có phải owner ko?
    permission_lookup = {'course_id': Course} 

    # 2. Output DTO Configuration (Cho Mixin)
    # Vì logic này chỉ dành cho Instructor, ta set giống nhau hoặc chỉ set instructor
    output_dto_public = CourseHealthOverviewOutput # Fallback
    output_dto_instructor = CourseHealthOverviewOutput
    output_dto_admin = CourseHealthOverviewOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics_service = course_dashboard_service

    def get(self, request, course_id, *args, **kwargs):
        """
        Flow: Service -> Domain -> Response -> Mixin (DTO Output)
        """
        try:
            # Service trả về Domain Object (CourseHealthOverviewDomain)
            overview_domain = self.analytics_service.get_course_health_overview(
                course_id=str(course_id)
            )
            
            # Trả về key "instance" để RoleBasedOutputMixin nhận diện và serialize sang DTO
            return Response(
                {"instance": overview_domain}, 
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            # Lỗi logic (ví dụ course_id ko hợp lệ format)
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Lỗi Server / Database
            logger.error(f"Lỗi trong CourseHealthOverviewView (GET): {e}", exc_info=True)
            return Response(
                {"detail": f"Lỗi máy chủ khi lấy dữ liệu analytics: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class InstructorCourseAnalyticsTrendsView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /api/courses/<course_id>/trends/
    Lấy dữ liệu biểu đồ (Line Chart) và phân tích xu hướng (7 ngày qua).
    """
    # 1. Permission & Security
    permission_classes = [IsInstructor] # Chỉ Instructor mới được xem
    
    # Tự động check: Course có tồn tại ko? User hiện tại có phải owner ko?
    permission_lookup = {'course_id': Course} 

    # 2. Output DTO Configuration (Cho Mixin)
    # API này chỉ dành cho Instructor
    output_dto_public = CourseTrendOutput # Fallback
    output_dto_instructor = CourseTrendOutput
    output_dto_admin = CourseTrendOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics_service = course_dashboard_service

    def get(self, request, course_id, *args, **kwargs):
        """
        Flow: Service -> Domain -> Response -> Mixin (DTO Output)
        """
        try:
            # Service trả về Domain Object (CourseTrendDomain)
            trend_domain = self.analytics_service.get_course_trends(
                course_id=str(course_id)
            )
            
            # Trả về key "instance" để RoleBasedOutputMixin nhận diện và serialize sang DTO
            return Response(
                {"instance": trend_domain}, 
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            # Lỗi logic (ví dụ course_id ko hợp lệ format)
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Lỗi Server / Database
            logger.error(f"Lỗi trong CourseAnalyticsTrendsView (GET): {e}", exc_info=True)
            return Response(
                {"detail": f"Lỗi máy chủ khi lấy dữ liệu trends: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InstructorCourseStudentsRiskListView(RoleBasedOutputMixin, AutoPermissionCheckMixin, PaginationMixin, APIView):
    """
    GET /instructor/courses/<course_id>/students-risk-list/
    """
    permission_classes = [IsInstructor]
    permission_lookup = {'course_id': Course}
    
    output_dto_public = StudentRiskInfoOutput
    output_dto_instructor = StudentRiskInfoOutput
    output_dto_admin = StudentRiskInfoOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics_service = course_dashboard_service

    def _safe_get_int(self, query_params, key, default):
        """Helper để parse int an toàn, tránh lỗi 500 ngớ ngẩn."""
        try:
            value = query_params.get(key, default)
            return int(value)
        except (ValueError, TypeError):
            return default

    def get(self, request, course_id, *args, **kwargs):
        try:
            # ---------------------------------------------------------
            # 1. INPUT VALIDATION (An toàn tuyệt đối)
            # ---------------------------------------------------------
            page = self._safe_get_int(request.query_params, 'page', 1)
            page_size = self._safe_get_int(request.query_params, 'page_size', 20)
            
            risk_filter = request.query_params.get('risk_level', 'all')
            search_term = request.query_params.get('search', '').strip()

            # ---------------------------------------------------------
            # 2. GET QUERYSET (Lazy Loading)
            # ---------------------------------------------------------
            queryset = self.analytics_service.get_student_risks_queryset(
                course_id=str(course_id)
            )
            
            # ---------------------------------------------------------
            # 3. FILTERING (Presentation Logic)
            # ---------------------------------------------------------
            if risk_filter and risk_filter != 'all':
                # Hỗ trợ list ?risk_level=high,critical
                risks = risk_filter.split(',')
                queryset = queryset.filter(risk_level__in=risks)

            if search_term:
                queryset = queryset.filter(
                    Q(user__email__icontains=search_term) | 
                    Q(user__username__icontains=search_term)
                )
                
            # ---------------------------------------------------------
            # 4. PAGINATION & EXECUTION (Mixin Logic)
            # ---------------------------------------------------------
            # SQL LIMIT/OFFSET chạy tại đây.
            # Trả về: {'items': [ModelInstances], 'meta': ...}
            # Chúng ta override request.query_params tạm thời hoặc truyền tham số vào hàm paginate nếu Mixin hỗ trợ
            # Ở đây giả sử Mixin lấy từ request, nhưng ta đã validate ở trên. 
            # Để an toàn nhất, ta dùng hàm paginate thủ công của Mixin với queryset đã filter
            
            # NOTE: Để đảm bảo Mixin dùng đúng page/page_size đã validate, 
            # ta nên update lại query_params (hoặc sửa Mixin để nhận tham số). 
            # Nhưng đơn giản nhất là để Mixin tự parse lại (nó cũng có try-catch).
            paginated_result = self.paginate_queryset(queryset, request)

            
            
            # ---------------------------------------------------------
            # 5. DOMAIN MAPPING (Model -> Domain)
            # ---------------------------------------------------------  
            domain_items = []
            for model_instance in paginated_result['items']:
                # Gọi thẳng vào Domain để transform
                domain_obj = StudentRiskInfoDomain.from_snapshot_model(model_instance, str(course_id))
                if domain_obj:
                    domain_items.append(domain_obj)

            # Thay thế list Model bằng list Domain
            paginated_result['items'] = domain_items

            # 5. Return Response
            # RoleBasedOutputMixin sẽ nhận dict này, thấy key 'items',
            # và map từng Domain Object sang DTO (StudentRiskInfoOutput)
            return Response(paginated_result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching student risks: {e}", exc_info=True)
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)