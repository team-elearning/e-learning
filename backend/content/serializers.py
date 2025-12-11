# # content/serializers.py
# from typing import Any, Dict, List, Optional
# from django.contrib.auth import get_user_model
from rest_framework import serializers
# from datetime import datetime, timedelta


from content.models import Module, Category, Tag, Subject, Course, ContentBlock, Lesson
from quiz.serializers import QuizUpdateMetadataSerializer
# from content.domains.subject_domain import SubjectDomain
# from content.domains.course_domain import CourseDomain
# from content.domains.lesson_domain import LessonDomain
# from content.domains.lesson_version_domain import LessonVersionDomain
# from content.domains.content_block_domain import ContentBlockDomain
# from content.domains.exploration_domain import ExplorationDomain, ExplorationTransitionDomain, ExplorationStateDomain
# from content.domains.commands import ChangeVersionStatusCommand, ReorderContentBlocksCommand, ReorderLessonsCommand, ReorderModulesCommand
# from quiz.models import Question
# User = get_user_model()


# # ----------------------- 
# # Helpers
# # -----------------------
# def _maybe_pk_to_id(obj):
#     """If obj is a model instance or a pk, return string id or None."""
#     if obj is None:
#         return None
#     if hasattr(obj, "id"):
#         return str(obj.id)
#     return str(obj)


# # -----------------------
# # Model Serializers (read/write that map Model <-> Domain)
# # -----------------------

# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ["id", "name", "slug"]
#         read_only_fields = ["id"]

# class TagSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Tag
#         fields = ["id", "name", "slug"]
#         read_only_fields = ["id"]


# class CourseSerializer(serializers.ModelSerializer):
#     id = serializers.UUIDField(read_only=True)
#     subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), allow_null=True, required=False)
#     owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True, required=False)
#     title = serializers.CharField(max_length=255)
#     description = serializers.CharField(allow_blank=True, required=False)
#     grade = serializers.CharField(max_length=16, allow_blank=True, required=False)
#     slug = serializers.SlugField(max_length=255, required=False, allow_null=True)
#     published = serializers.BooleanField(default=False)
#     published_at = serializers.DateTimeField(read_only=True)
#     categories = CategorySerializer(many=True, read_only=True)
#     tags = TagSerializer(many=True, read_only=True)

#     class Meta:
#         model = Course
#         fields = ["id", "subject", "title", "description", "grade", "owner", "slug", "published", "published_at", "categories", "tags"]
#         read_only_fields = ["id", "published_at"]

#     def to_domain(self) -> CourseDomain:
#         """
#         Convert validated_data -> CourseDomain (for create/update commands).
#         We pass subject_id and owner_id as strings/ints for the domain.
#         """
#         d = self.validated_data
#         subject = d.get("subject")
#         owner = d.get("owner")
#         course = CourseDomain(
#             title=d["title"],
#             subject_id=_maybe_pk_to_id(subject),
#             description=d.get("description"),
#             grade=d.get("grade"),
#             owner_id=(owner.id if owner else None),
#             slug=d.get("slug")
#         )
#         course.validate()
#         return course

#     @staticmethod
#     def from_domain(domain: CourseDomain) -> Dict[str, Any]:
#         return domain.to_dict()


# class ModuleSerializer(serializers.ModelSerializer):
#     """
#     Serializer cho PATCH (cập nhật một phần).
#     Dùng để validate các trường trong body.
#     Tất cả các trường đều là không bắt buộc (required=False).
#     """
#     class Meta:
#         model = Module
#         fields = [
#             'title', 
#             'position'
#         ]
#         extra_kwargs = {
#             'title': {'required': False},
#             'position': {'required': False},
#         }


# class ContentBlockSerializer(serializers.ModelSerializer):
#     id = serializers.UUIDField(required=False, allow_null=True)
#     lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all(), required=False, source="lesson_version_id")
#     type = serializers.ChoiceField(choices=[("text", "Text"), ("image", "Image"), ("video", "Video"), ("quiz", "Quiz"), ("exploration_ref", "ExplorationRef")])
#     position = serializers.IntegerField(default=0, min_value=0)
#     payload = serializers.JSONField()

#     class Meta:
#         model = ContentBlock
#         fields = ["id", "lesson_version", "type", "position", "payload"]
#         read_only_fields = ["id"]

#     def to_domain(self) -> ContentBlockDomain:
#         d = self.validated_data
#         lesson_version = d.get("lesson_version")  # this will be a LessonVersion model instance or PK depending on DRF
#         # map to lesson_version_id
#         lesson_version_id = _maybe_pk_to_id(lesson_version)
#         cb = ContentBlockDomain(
#             lesson_version_id=lesson_version_id,
#             type=d["type"],
#             position=d.get("position", 0),
#             payload=d.get("payload", {})
#         )
#         cb.validate_payload()
#         return cb

#     @staticmethod
#     def from_domain(domain: ContentBlockDomain) -> Dict[str, Any]:
#         return domain.to_dict()


# # class LessonVersionSerializer(serializers.ModelSerializer):
# #     id = serializers.UUIDField(read_only=True)
# #     lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all(), source="lesson_id")
# #     version = serializers.IntegerField(read_only=True)
# #     status = serializers.ChoiceField(choices=[("draft", "Draft"), ("review", "Review"), ("published", "Published")], default="draft")
# #     author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True, required=False)
# #     content = serializers.JSONField()
# #     change_summary = serializers.CharField(allow_blank=True, required=False)
# #     created_at = serializers.DateTimeField(read_only=True)
# #     published_at = serializers.DateTimeField(read_only=True)
# #     # nested read-only list of content blocks (if prefetched)
# #     content_blocks = ContentBlockSerializer(many=True, read_only=True)

# #     class Meta:
# #         model = LessonVersion
# #         fields = ["id", "lesson", "version", "status", "author", "content", "change_summary", "created_at", "published_at", "content_blocks"]
# #         read_only_fields = ["id", "version", "created_at", "published_at", "content_blocks"]

#     # def to_domain(self) -> LessonVersionDomain:
#     #     """
#     #     For creation/updating of lesson versions.
#     #     If instance exists, it's an update; for create, version will be assigned by domain/Service.
#     #     """

#     #     d = self.validated_data
#     #     lesson = d.get("lesson")
#     #     lesson_id = _maybe_pk_to_id(lesson)
#     #     author = d.get("author")
#     #     lv = LessonVersionDomain(
#     #         lesson_id=lesson_id,
#     #         version=d.get("version", 0) or 0,  # service will set real version on create
#     #         status=d.get("status", "draft"),
#     #         author_id=(author.id if author else None),
#     #         content=d.get("content", {}),
#     #         change_summary=d.get("change_summary")
#     #     )
#     #     # Validate content structure (this will validate content blocks payload)
#     #     lv.validate_content()
#     #     return lv

#     # @staticmethod
#     # def from_domain(domain: LessonVersionDomain) -> Dict[str, Any]:
#     #     return domain.to_dict()


# class LessonSerializer(serializers.ModelSerializer):
#     id = serializers.UUIDField(required = False)
#     module = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all(), source="module_id")
#     title = serializers.CharField(max_length=255)
#     position = serializers.IntegerField(default=0, min_value=0)
#     content_type = serializers.ChoiceField(choices=[("lesson", "Lesson"), ("exploration", "Exploration"), ("exercise", "Exercise"), ("quiz", "Quiz")], default="lesson")
#     published = serializers.BooleanField(default=False)
#     # versions = LessonVersionSerializer(many=True, read_only=True)

#     class Meta:
#         model = Lesson
#         fields = ["id", "module", "title", "position", "content_type", "published"]
#         read_only_fields = ["id", "versions"]

#     def to_domain(self) -> LessonDomain:
#         d = self.validated_data
#         module = d.get("module")
#         lesson = LessonDomain(
#             module_id=_maybe_pk_to_id(module),
#             title=d["title"],
#             position=d.get("position", 0),
#             content_type=d.get("content_type", "lesson"),
#             published=d.get("published", False)
#         )
#         lesson.validate()
#         return lesson

#     @staticmethod
#     def from_domain(domain: LessonDomain) -> Dict[str, Any]:
#         return domain.to_dict()


# class SetStatusSerializer(serializers.Serializer):
#     """
#     Serializer này CHỈ dùng để validate đầu vào cho
#     action 'set_status'.
#     """
#     # Lấy các choices từ LessonVersionDomain của bạn
#     VALID_STATUSES = ("draft", "review", "published", "archived")
    
#     status = serializers.ChoiceField(choices=VALID_STATUSES)


# # class LessonVersionCreateSerializer(serializers.Serializer):
# #     """
# #     Serializer Input (Đầu vào) cho POST (Tạo mới) một Cụm LessonVersion.
# #     """
# #     change_summary = serializers.CharField(required=False, allow_blank=True)
# #     # Đây là nơi client gửi lên danh sách các block
# #     content_blocks = ContentBlockInputSerializer(many=True, required=False, default=[])
    

# # class LessonVersionUpdateSerializer(serializers.Serializer):
# #     """
# #     Serializer Input (Đầu vào) cho PATCH (Cập nhật) một Cụm LessonVersion.
# #     Tất cả các trường đều là 'required=False'.
# #     """
# #     change_summary = serializers.CharField(required=False, allow_blank=True)
    
# #     # 'content_blocks' cũng là optional.
# #     # Nếu client không gửi key này, service sẽ không đụng đến blocks.
# #     # Nếu client gửi key này (kể cả list rỗng), service sẽ "Sync" theo list đó.
# #     content_blocks = ContentBlockInputSerializer(many=True, required=False)


# # -----------------------
# # Command / Input-only Serializers (to produce Domain Command objects)
# # -----------------------
# # These are used by endpoints for create/publish actions and convert to domain commands

# class CreateCourseInputSerializer(serializers.Serializer):
#     title = serializers.CharField(max_length=255)
#     subject_id = serializers.UUIDField(required=False, allow_null=True)
#     description = serializers.CharField(required=False, allow_blank=True)
#     grade = serializers.CharField(max_length=16, required=False, allow_blank=True)
#     owner_id = serializers.IntegerField(required=False, allow_null=True) # Assuming user ID is int

#     def to_domain(self):
#         from content.domains.commands import CreateCourseCommand
#         d = self.validated_data
#         return CreateCourseCommand(
#             title=d['title'],
#             subject_id=str(d['subject_id']) if d.get('subject_id') else None,
#             description=d.get('description'),
#             grade=d.get('grade'),
#             owner_id=d.get('owner_id')
#         )

# class AddModuleInputSerializer(serializers.Serializer):
#     title = serializers.CharField(max_length=255)
#     position = serializers.IntegerField(required=False, min_value=0)

#     def to_domain(self, course_id: str):
#         from content.domains.commands import AddModuleCommand
#         d = self.validated_data
#         return AddModuleCommand(
#             course_id=course_id,
#             title=d['title'],
#             position=d.get('position')
#         )

# class CreateLessonInputSerializer(serializers.Serializer):
#     title = serializers.CharField(max_length=255)
#     position = serializers.IntegerField(required=False, min_value=0)
#     content_type = serializers.ChoiceField(choices=LessonDomain.VALID_CONTENT_TYPES, default='lesson')

#     def to_domain(self, module_id: str):
#         from content.domains.commands import CreateLessonCommand
#         d = self.validated_data
#         return CreateLessonCommand(
#             module_id=module_id,
#             title=d['title'],
#             position=d.get('position'),
#             content_type=d.get('content_type')
#         )

# class CreateLessonVersionInputSerializer(serializers.Serializer):
#     author_id = serializers.IntegerField(required=False, allow_null=True)
#     content = serializers.JSONField()
#     change_summary = serializers.CharField(required=False, allow_blank=True)

#     def to_domain(self, lesson_id: str):
#         from content.domains.commands import CreateLessonVersionCommand
#         d = self.validated_data
#         return CreateLessonVersionCommand(
#             lesson_id=lesson_id,
#             author_id=d.get('author_id'),
#             content=d['content'],
#             change_summary=d.get('change_summary')
#         )

# class PublishLessonVersionInputSerializer(serializers.Serializer):
#     version = serializers.IntegerField(min_value=1)
#     publish_comment = serializers.CharField(required=False, allow_blank=True)

#     def to_domain(self, lesson_id: str):
#         from content.domains.commands import PublishLessonVersionCommand
#         d = self.validated_data
#         return PublishLessonVersionCommand(
#             lesson_id=lesson_id,
#             version=d['version'],
#             publish_comment=d.get('publish_comment')
#         )

# class ContentBlockCreateSerializer(serializers.Serializer):
#     type = serializers.ChoiceField(choices=ContentBlockDomain.VALID_TYPES)
#     position = serializers.IntegerField(required=False, min_value=0)
#     payload = serializers.JSONField()

#     def to_domain(self, lesson_version_id: str):
#         from content.domains.commands import AddContentBlockCommand
#         d = self.validated_data
#         return AddContentBlockCommand(
#             lesson_version_id=lesson_version_id,
#             type=d['type'],
#             position=d.get('position'),
#             payload=d['payload']
#         )

# class CreateExplorationInputSerializer(serializers.Serializer):
#     title = serializers.CharField(max_length=255)
#     owner_id = serializers.IntegerField(required=False, allow_null=True)
#     language = serializers.CharField(max_length=8, default='vi')

#     def to_domain(self):
#         from content.domains.commands import CreateExplorationCommand
#         d = self.validated_data
#         return CreateExplorationCommand(
#             title=d['title'],
#             owner_id=d.get('owner_id'),
#             language=d.get('language')
#         )

# class AddExplorationStateInputSerializer(serializers.Serializer):
#     name = serializers.CharField(max_length=255)
#     content = serializers.JSONField()
#     interaction = serializers.JSONField()

#     def to_domain(self, exploration_id: str):
#         from content.domains.commands import AddExplorationStateCommand
#         d = self.validated_data
#         return AddExplorationStateCommand(
#             exploration_id=exploration_id,
#             name=d['name'],
#             content=d['content'],
#             interaction=d['interaction']
#         )

# class AddExplorationTransitionInputSerializer(serializers.Serializer):
#     from_state = serializers.CharField(max_length=255)
#     to_state = serializers.CharField(max_length=255)
#     condition = serializers.JSONField()

#     def to_domain(self, exploration_id: str):
#         from content.domains.commands import AddExplorationTransitionCommand
#         d = self.validated_data
#         return AddExplorationTransitionCommand(
#             exploration_id=exploration_id,
#             from_state=d['from_state'],
#             to_state=d['to_state'],
#             condition=d['condition']
#         )

# class ChangeVersionStatusInputSerializer(serializers.Serializer):
#     status = serializers.ChoiceField(choices=LessonVersionDomain.VALID_STATUSES)

#     def to_domain(self) -> ChangeVersionStatusCommand:
#         return ChangeVersionStatusCommand(status=self.validated_data['status'])

# class ReorderItemSerializer(serializers.Serializer):
#     id = serializers.CharField()
#     position = serializers.IntegerField()

# class ReorderItemsInputSerializer(serializers.Serializer):
#     items = ReorderItemSerializer(many=True)

#     def to_domain(self, reorder_type: str):
#         order_map = {item['id']: item['position'] for item in self.validated_data['items']}
#         if reorder_type == 'modules':
#             return ReorderModulesCommand(order_map=order_map)
#         if reorder_type == 'lessons':
#             return ReorderLessonsCommand(order_map=order_map)
#         if reorder_type == 'blocks':
#             return ReorderContentBlocksCommand(order_map=order_map)
#         raise ValueError("Invalid reorder type")
    

# ##########################################################################################################################################################################
class SubjectSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=255, required = False)

    class Meta:
        model = Subject
        fields = ["id", "title", "slug"]
        read_only_fields = ["id"]


class ContentBlockCreateSerializer(serializers.Serializer):
    """
    Dùng riêng cho POST: Chỉ cần biết loại block để tạo khung xương (Skeleton).
    Không validate payload chi tiết ở bước này.
    """
    type = serializers.ChoiceField(
        choices=[c[0] for c in ContentBlock._meta.get_field('type').choices],
        required=True
    )
    position = serializers.IntegerField(required=False, min_value=0)
    # Payload cho phép rỗng hoặc dict tùy ý, không validate sâu
    payload = serializers.DictField(required=False, default=dict)


class ContentBlockUpdateSerializer(serializers.Serializer):
    """
    Serializer con, KHÔNG PHẢI ModelSerializer.
    Dùng để validate từng block trong danh sách 'content_blocks'
    """
    # 'id' là Optional. 
    # - Nếu có (UUID), service sẽ hiểu là CẬP NHẬT.
    # - Nếu không có (None), service sẽ hiểu là TẠO MỚI.
    id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    type = serializers.ChoiceField(choices=[c[0] for c in ContentBlock._meta.get_field('type').choices])
    payload = serializers.DictField(default=dict, required=False)

    def validate(self, attrs):
        block_type = attrs.get('type')
        payload = attrs.get('payload', {})

        # --- VALIDATE RICH TEXT ---
        if block_type == 'rich_text':
            # SỬA: Dùng 'html_content' để khớp với Service
            if not payload.get('html_content'):
                raise serializers.ValidationError({
                    "payload": "Loại 'rich_text' yêu cầu field 'html_content' trong payload."
                })

        # --- VALIDATE QUIZ ---
        elif block_type == 'quiz':
            # Giả định QuizCourseSerializer đã được import
            # Validate cấu trúc đề thi/cài đặt quiz
            quiz_serializer = QuizUpdateMetadataSerializer(data=payload)
            quiz_serializer.is_valid(raise_exception=True)
            
            # Gán lại data sạch đã validate vào attrs
            attrs['payload'] = quiz_serializer.validated_data

        # --- VALIDATE MEDIA/FILES ---
        else:
            # Map này PHẢI khớp với 'single_file_map' trong Service
            file_key_map = {
                'video': 'video_id',
                'pdf':   'file_id',
                'docx':  'file_id',
                'file':  'file_id',
                # 'image': 'image_id' (Nếu model thêm image thì mở comment này)
            }

            if block_type in file_key_map:
                required_key = file_key_map[block_type]
                if not payload.get(required_key):
                    raise serializers.ValidationError({
                        "payload": f"Loại '{block_type}' yêu cầu field '{required_key}' trong payload."
                    })

        return attrs
    

class ContentBlockReorderSerializer(serializers.Serializer):
    """
    Validate danh sách ID block gửi lên để sắp xếp.
    """
    block_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="Danh sách ID của các block theo thứ tự mới"
    )


class ConvertBlockSerializer(serializers.Serializer):
    """
    Validate payload cho API chuyển đổi loại block.
    Example: {"target_type": "video"}
    """
    target_type = serializers.ChoiceField(
        choices=[c[0] for c in ContentBlock._meta.get_field('type').choices],
        required=True,
        help_text="Loại block mới muốn chuyển sang."
    )
    

class LessonSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False)
    content_blocks = ContentBlockCreateSerializer(many=True, required=False, allow_null=True)


class LessonReorderSerializer(serializers.Serializer):
    """
    Serializer cho hành động reorder.
    Chỉ dùng để validate payload: {"lesson_ids": ["uuid-1", ...]}
    """
    lesson_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="Danh sách ID của các lesson theo thứ tự mới"
    )


class ModuleSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    lessons = LessonSerializer(many=True, required=False, allow_empty=True)


class ModuleReorderSerializer(serializers.Serializer):
    """
    Serializer cho hành động reorder.
    Chỉ dùng để validate payload: {"module_ids": ["uuid-1", ...]}
    """
    module_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="Danh sách ID của các module theo thứ tự mới"
    )


class CourseSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False)
    slug = serializers.SlugField(max_length=255, required=False, allow_blank=True)
    image_id = serializers.CharField(max_length=1024, required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    subject = serializers.CharField(required=False)
    categories = serializers.ListField(child=serializers.CharField(max_length=255), required=False, allow_empty=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=255), required=False, allow_empty=True)
    grade = serializers.CharField(max_length=16, required=False, allow_blank=True)
    published = serializers.BooleanField(default=False)
    modules = ModuleSerializer(many=True, required=False, allow_empty=True)


class EnrollmentCreateSerializer(serializers.Serializer):
    """
    Validate JSON input thô từ client: { "user_id": "..." }
    """
    user_id = serializers.UUIDField(required=True)



