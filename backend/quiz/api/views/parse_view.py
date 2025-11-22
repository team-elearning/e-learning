from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from core.api.permissions import IsInstructor
from quiz.services.quiz_parser_service import parse_excel, parse_docx, parse_csv



class QuizParseToolView(APIView):
    """
    API tiện ích: Upload file -> Trả về JSON câu hỏi.
    Frontend dùng JSON này để hiển thị cho giáo viên sửa trước khi lưu.
    ENDPOINT: /api/tools/quiz-parser/
    """
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        file_obj = request.FILES.get('file')
        file_type = request.data.get('type', '').lower() # 'excel' | 'csv' | 'word'

        if not file_obj:
            return Response({"detail": "Thiếu file."}, status=400)
 
        try:
            if file_type == 'excel':
                data = parse_excel(file_obj)
            elif file_type in ['csv']:
                data = parse_csv(file_obj)
            elif file_type == 'word':
                data = parse_docx(file_obj)
            else:
                return Response({"detail": "Loại file không hỗ trợ."}, status=400)
            
            # Trả về JSON để Frontend tự xử
            return Response({
                "questions": data,
                "total_parsed": len(data) # Optional: Trả thêm cái này để FE tiện hiển thị thông báo
            }, status=200)

        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        except Exception as e:
            # Logger...
            return Response({"detail": f"Lỗi xử lý file - {str(e)}"}, status=500)