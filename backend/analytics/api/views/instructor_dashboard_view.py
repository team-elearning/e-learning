import logging
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.api.permissions import IsInstructor
from core.api.mixins import RoleBasedOutputMixin, AutoPermissionCheckMixin, PaginationMixin
from content.models import Course
from analytics.api.dtos.analytics_dto import CourseHealthOverviewOutput, CourseTrendOutput, StudentRiskInfoOutput
from analytics.services import instructor_course_dashboard_service
from analytics.domains.student_risk_info_domain import StudentRiskInfoDomain



logger = logging.getLogger(__name__)

class CourseHealthOverviewView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /api/courses/<course_id>/analytics/overview/
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
        self.analytics_service = instructor_course_dashboard_service

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
        

class CourseAnalyticsTrendsView(RoleBasedOutputMixin, AutoPermissionCheckMixin, APIView):
    """
    GET /api/courses/<course_id>/analytics/trends/
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
        self.analytics_service = instructor_course_dashboard_service

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


class CourseStudentsRiskListView(RoleBasedOutputMixin, AutoPermissionCheckMixin, PaginationMixin, APIView):
    """
    GET /api/courses/<course_id>/analytics/students/
    """
    permission_classes = [IsInstructor]
    permission_lookup = {'course_id': Course}
    
    output_dto_public = StudentRiskInfoOutput
    output_dto_instructor = StudentRiskInfoOutput
    output_dto_admin = StudentRiskInfoOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics_service = instructor_course_dashboard_service

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