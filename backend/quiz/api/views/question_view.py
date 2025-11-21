class QuizQuestionManagerView(APIView):
    """
    Quản lý câu hỏi bên trong một Quiz cụ thể.
    ENDPOINT: /api/instructor/quizzes/<quiz_id>/questions/
    
    (Lưu ý: quiz_id ở đây có thể là ID của Exam hoặc Practice)
    """
    permission_classes = [IsAuthenticated, IsInstructor]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question_service = question_service

    def get(self, request, quiz_id, *args, **kwargs):
        """ Lấy danh sách câu hỏi của Quiz này (kèm prompt, options) """
        try:
            questions = self.question_service.list_questions_by_quiz(
                user=request.user, quiz_id=quiz_id
            )
            # Trả về list DTO chứa prompt, answer_payload đầy đủ để Frontend render form
            return Response(questions, status=status.HTTP_200_OK)
        except Exception as e:
             return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, quiz_id, *args, **kwargs):
        """
        Thêm câu hỏi mới vào Quiz.
        Payload mẫu cho field 'prompt' (JSON):
        {
            "type": "multiple_choice_single",
            "prompt": {
                "text": "Thủ đô của Việt Nam là gì?",
                "options": [
                     {"id": "A", "text": "Hà Nội"},
                     {"id": "B", "text": "HCM"}
                ]
            },
            "answer_payload": { "correct_ids": ["A"] },
            "score": 1.0
        }
        """
        serializer = QuestionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Service cần handle việc parse JSON prompt vào model Question
            new_question = self.question_service.add_question_to_quiz(
                user=request.user,
                quiz_id=quiz_id,
                data=serializer.validated_data
            )
            return Response(new_question, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class QuizQuestionDetailView(APIView):
    """
    Sửa/Xóa từng câu hỏi cụ thể.
    ENDPOINT: /api/instructor/questions/<question_id>/
    """
    permission_classes = [IsAuthenticated, IsInstructor]

    def put(self, request, question_id, *args, **kwargs):
        """ Update nội dung câu hỏi (Sửa prompt, sửa đáp án đúng) """
        # Logic tương tự POST, gọi service.update_question(...)
        pass

    def delete(self, request, question_id, *args, **kwargs):
        """ Xóa câu hỏi khỏi đề """
        # Logic gọi service.delete_question(...)
        pass