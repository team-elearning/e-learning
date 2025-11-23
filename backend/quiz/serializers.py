from rest_framework import serializers

from quiz.models import Quiz, Question, UserAnswer



class QuestionInputSerializer(serializers.Serializer):
    """
    Serializer cho từng câu hỏi bên trong mảng 'questions'
    """
    id = serializers.UUIDField(required=False, allow_null=True) # Có ID -> Update, Không ID -> Create
    
    # Validate loại câu hỏi theo choices trong Model
    type = serializers.ChoiceField(choices=Question.QUESTION_TYPES)
    
    # JSON Fields: DRF dùng DictField để hứng JSON object
    prompt = serializers.DictField(
        required=True, 
        help_text="Nội dung câu hỏi: {text, image_url, options...}"
    )
    answer_payload = serializers.DictField(
        required=True, 
        help_text="Đáp án đúng: {correct_ids: [...]}"
    )
    hint = serializers.DictField(required=False, default=dict)
    
    position = serializers.IntegerField(required=False, default=0)

    def validate(self, data):
        """
        Validate logic nội bộ câu hỏi (Optional).
        Ví dụ: Nếu là trắc nghiệm thì trong prompt phải có 'options'.
        """
        q_type = data.get('type')
        prompt = data.get('prompt')

        # Logic check sơ bộ (Moodle style strict checking)
        if 'multiple_choice' in q_type:
            if 'options' not in prompt or not isinstance(prompt['options'], list):
                raise serializers.ValidationError({
                    "prompt": "Loại câu hỏi trắc nghiệm bắt buộc phải có danh sách 'options' trong prompt."
                })
        
        return data
    

class ExamInputSerializer(serializers.Serializer):
    """
    Big JSON Serializer để Tạo/Cập nhật Bài thi (Exam).
    Field 'mode' được ẩn vì Service sẽ tự set là 'exam'.
    """
    # --- 1. Thông tin chung ---
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)

    # --- 2. Cấu hình Thời gian ---
    # DurationField nhận chuỗi dạng "HH:MM:SS" (vd: "00:45:00") hoặc số giây
    time_limit = serializers.DurationField(required=False, allow_null=True) 
    
    time_open = serializers.DateTimeField(required=False, allow_null=True)
    time_close = serializers.DateTimeField(required=False, allow_null=True)

    # --- 3. Cấu hình Quy tắc ---
    # Exam thường khắt khe: max_attempts thường là 1
    max_attempts = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    pass_score = serializers.DecimalField(max_digits=4, decimal_places=2, required=False, allow_null=True)
    
    # Random & Shuffle
    questions_count = serializers.IntegerField(min_value=0, required=False, default=10)
    shuffle_questions = serializers.BooleanField(default=True)

    # Grading & Review
    grading_method = serializers.ChoiceField(choices=Quiz.GRADING_METHOD, default='highest')
    show_correct_answer = serializers.BooleanField(default=False) # Exam mặc định nên ẩn

    # --- 4. Nested Questions (Quan trọng) ---
    # Cho phép tạo bài thi kèm luôn danh sách câu hỏi
    questions = QuestionInputSerializer(many=True, required=False, allow_empty=True)

    def validate(self, data):
        """
        Validate logic chéo giữa các fields (Cross-field validation)
        """
        time_open = data.get('time_open')
        time_close = data.get('time_close')

        # 1. Logic ngày tháng
        if time_open and time_close and time_open > time_close:
            raise serializers.ValidationError({
                "time_close": "Thời gian đóng phải diễn ra SAU thời gian mở."
            })

        # 2. Logic Questions Count (Optional warning logic)
        # questions = data.get('questions', [])
        # questions_count = data.get('questions_count', 0)
        # if questions and 0 < len(questions) < questions_count:
            # Có thể raise warning hoặc error tùy độ khó tính
            # raise serializers.ValidationError({
            #     "questions_count": f"Bạn yêu cầu random {questions_count} câu nhưng chỉ nạp vào {len(questions)} câu."
            # })

        return data
    

class PracticeInputSerializer(serializers.Serializer):
    """
    Big JSON Serializer để Tạo/Cập nhật Bài thi (Exam).
    Field 'mode' được ẩn vì Service sẽ tự set là 'exam'.
    """
    # --- 1. Thông tin chung ---
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)

    # --- 2. Cấu hình Thời gian ---
    # DurationField nhận chuỗi dạng "HH:MM:SS" (vd: "00:45:00") hoặc số giây
    time_limit = serializers.DurationField(required=False, allow_null=True) 
    
    time_open = serializers.DateTimeField(required=False, allow_null=True)
    time_close = serializers.DateTimeField(required=False, allow_null=True)

    # --- 3. Cấu hình Quy tắc ---
    # Exam thường khắt khe: max_attempts thường là 1
    max_attempts = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    pass_score = serializers.DecimalField(max_digits=4, decimal_places=2, required=False, allow_null=True)
    
    # Random & Shuffle
    questions_count = serializers.IntegerField(min_value=0, required=False, default=10)
    shuffle_questions = serializers.BooleanField(default=True)

    # Grading & Review
    grading_method = serializers.ChoiceField(choices=Quiz.GRADING_METHOD, default='highest')
    show_correct_answer = serializers.BooleanField(default=True)

    # --- 4. Nested Questions (Quan trọng) ---
    # Cho phép tạo bài thi kèm luôn danh sách câu hỏi
    questions = QuestionInputSerializer(many=True, required=False, allow_empty=True)

    def validate(self, data):
        """
        Validate logic chéo giữa các fields (Cross-field validation)
        """
        time_open = data.get('time_open')
        time_close = data.get('time_close')

        # 1. Logic ngày tháng
        if time_open and time_close and time_open > time_close:
            raise serializers.ValidationError({
                "time_close": "Thời gian đóng phải diễn ra SAU thời gian mở."
            })

        # 2. Logic Questions Count (Optional warning logic)
        # questions = data.get('questions', [])
        # questions_count = data.get('questions_count', 0)
        # if questions and 0 < len(questions) < questions_count:
            # Có thể raise warning hoặc error tùy độ khó tính
            # raise serializers.ValidationError({
            #     "questions_count": f"Bạn yêu cầu random {questions_count} câu nhưng chỉ nạp vào {len(questions)} câu."
            # })

        return data
    

class QuestionTakingSerializer(serializers.ModelSerializer):
    """
    Dùng cho màn hình LÀM BÀI.
    Tuyệt đối KHÔNG include 'answer_payload', 'hint', 'explanation'.
    """
    class Meta:
        model = Question
        fields = ['id', 'type', 'prompt'] # Chỉ trả về nội dung câu hỏi


class UserAnswerDetailSerializer(serializers.ModelSerializer):
    # Dùng cho màn hình KẾT QUẢ
    question_prompt = serializers.ReadOnlyField(source='question.prompt')
    question_explanation = serializers.SerializerMethodField()
    correct_answer = serializers.SerializerMethodField()

    class Meta:
        model = UserAnswer
        fields = ['question_id', 'question_prompt', 'selected_options', 'is_correct', 'score_obtained', 'question_explanation', 'correct_answer']

    def get_question_explanation(self, obj):
        # Chỉ hiện giải thích nếu mode là Practice hoặc settings cho phép
        if obj.attempt.quiz.mode == 'practice' or obj.attempt.quiz.show_correct_answer:
            return obj.question.hint
        return None

    def get_correct_answer(self, obj):
        if obj.attempt.quiz.mode == 'practice' or obj.attempt.quiz.show_correct_answer:
            return obj.question.answer_payload
        return None