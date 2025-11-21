class InstructorPracticeListView(RoleBasedOutputMixin, APIView):
    """
    API quản lý bộ đề luyện tập.
    ENDPOINT: /api/instructor/practices/
    """
    permission_classes = [IsAuthenticated, IsInstructor]
    output_dto_public = PracticeListOutput # DTO này có thể hiện trường 'max_attempts'
    output_dto_admin = PracticeListOutput

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.practice_service = practice_service 

    def get(self, request, *args, **kwargs):
        practices = self.practice_service.list_my_practices(user=request.user)
        return Response({"results": practices}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Tạo bộ luyện tập mới.
        Service sẽ TỰ ĐỘNG set:
        - mode = 'practice'
        - max_attempts = None (hoặc theo input nhưng thường là None)
        - grading_method = 'highest'
        - show_correct_answer = True
        """
        serializer = PracticeInputSerializer(data=request.data)
        # ... (Logic validate tương tự Exam nhưng dùng PracticeInputSerializer)
        
        try:
            dto = QuizCreateInput(**serializer.validated_data)
            new_practice = self.practice_service.create_practice(
                user=request.user, data=dto.model_dump()
            )
            return Response({"instance": new_practice}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Class InstructorPracticeDetailView tương tự ExamDetailView nhưng gọi practice_service