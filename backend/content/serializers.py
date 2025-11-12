# content/serializers.py
from typing import Any, Dict, List, Optional
from django.contrib.auth import get_user_model
from rest_framework import serializers

from content.models import Module, Category, Tag, Subject, Course, LessonVersion, ContentBlock, Lesson, Exploration, ExplorationState, ExplorationTransition, AnswerGroup, Hint, Solution, RuleSpec
from content.domains.subject_domain import SubjectDomain
from content.domains.course_domain import CourseDomain
from content.domains.lesson_domain import LessonDomain
from content.domains.lesson_version_domain import LessonVersionDomain
from content.domains.content_block_domain import ContentBlockDomain
from content.domains.exploration_domain import ExplorationDomain, ExplorationTransitionDomain, ExplorationStateDomain
from content.domains.commands import ChangeVersionStatusCommand, ReorderContentBlocksCommand, ReorderLessonsCommand, ReorderModulesCommand
User = get_user_model()


# -----------------------
# Helpers
# -----------------------
def _maybe_pk_to_id(obj):
    """If obj is a model instance or a pk, return string id or None."""
    if obj is None:
        return None
    if hasattr(obj, "id"):
        return str(obj.id)
    return str(obj)


# -----------------------
# Model Serializers (read/write that map Model <-> Domain)
# -----------------------

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]
        read_only_fields = ["id"]

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]
        read_only_fields = ["id"]

class SubjectSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=255)

    class Meta:
        model = Subject
        fields = ["id", "title", "slug"]
        read_only_fields = ["id"]

    def to_domain(self) -> SubjectDomain:
        """
        Convert serializer validated_data -> SubjectDomain.
        Caller should call is_valid() before.
        """
        data = self.validated_data
        domain = SubjectDomain(title=data["title"], slug=data["slug"])
        domain.validate()
        return domain

    @staticmethod
    def from_domain(domain: SubjectDomain) -> Dict[str, Any]:
        """Convert SubjectDomain -> primitive dict for API response."""
        return domain.to_dict()


class CourseSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), allow_null=True, required=False)
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True, required=False)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True, required=False)
    grade = serializers.CharField(max_length=16, allow_blank=True, required=False)
    slug = serializers.SlugField(max_length=255, required=False, allow_null=True)
    published = serializers.BooleanField(default=False)
    published_at = serializers.DateTimeField(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "subject", "title", "description", "grade", "owner", "slug", "published", "published_at", "categories", "tags"]
        read_only_fields = ["id", "published_at"]

    def to_domain(self) -> CourseDomain:
        """
        Convert validated_data -> CourseDomain (for create/update commands).
        We pass subject_id and owner_id as strings/ints for the domain.
        """
        d = self.validated_data
        subject = d.get("subject")
        owner = d.get("owner")
        course = CourseDomain(
            title=d["title"],
            subject_id=_maybe_pk_to_id(subject),
            description=d.get("description"),
            grade=d.get("grade"),
            owner_id=(owner.id if owner else None),
            slug=d.get("slug")
        )
        course.validate()
        return course

    @staticmethod
    def from_domain(domain: CourseDomain) -> Dict[str, Any]:
        return domain.to_dict()


class ModuleSerializer(serializers.ModelSerializer):
    """
    Serializer cho PATCH (cập nhật một phần).
    Dùng để validate các trường trong body.
    Tất cả các trường đều là không bắt buộc (required=False).
    """
    class Meta:
        model = Module
        fields = [
            'title', 
            'position'
        ]
        extra_kwargs = {
            'title': {'required': False},
            'position': {'required': False},
        }

class ModuleCreateSerializer(serializers.ModelSerializer):
    """
    Serializer cho POST (tạo mới) và PUT (cập nhật toàn bộ).
    Validate các trường bắt buộc trong body.
    """
    class Meta:
        model = Module
        fields = [
            'title', 
            'position'
        ]
        # course_id không có ở đây vì nó đến từ URL
        extra_kwargs = {
            'title': {'required': True},
            'position': {'required': False}, # Model có default
        }

class ModuleReorderSerializer(serializers.Serializer):
    """
    Serializer cho hành động reorder.
    Chỉ dùng để validate payload: {"module_ids": ["uuid-1", ...]}
    """
    module_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )


class ContentBlockSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    lesson_version = serializers.PrimaryKeyRelatedField(queryset=LessonVersion.objects.all(), source="lesson_version_id")
    type = serializers.ChoiceField(choices=[("text", "Text"), ("image", "Image"), ("video", "Video"), ("quiz", "Quiz"), ("exploration_ref", "ExplorationRef")])
    position = serializers.IntegerField(default=0, min_value=0)
    payload = serializers.JSONField()

    class Meta:
        model = ContentBlock
        fields = ["id", "lesson_version", "type", "position", "payload"]
        read_only_fields = ["id"]

    def to_domain(self) -> ContentBlockDomain:
        d = self.validated_data
        lesson_version = d.get("lesson_version")  # this will be a LessonVersion model instance or PK depending on DRF
        # map to lesson_version_id
        lesson_version_id = _maybe_pk_to_id(lesson_version)
        cb = ContentBlockDomain(
            lesson_version_id=lesson_version_id,
            type=d["type"],
            position=d.get("position", 0),
            payload=d.get("payload", {})
        )
        cb.validate_payload()
        return cb

    @staticmethod
    def from_domain(domain: ContentBlockDomain) -> Dict[str, Any]:
        return domain.to_dict()
    

class ReorderBlocksSerializer(serializers.Serializer):
    """
    Serializer này CHỈ dùng để validate payload cho việc sắp xếp lại.
    """
    ordered_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=True  # Cho phép gửi một list rỗng (nếu logic nghiệp vụ cho phép)
    )


class LessonVersionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all(), source="lesson_id")
    version = serializers.IntegerField(read_only=True)
    status = serializers.ChoiceField(choices=[("draft", "Draft"), ("review", "Review"), ("published", "Published")], default="draft")
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True, required=False)
    content = serializers.JSONField()
    change_summary = serializers.CharField(allow_blank=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    published_at = serializers.DateTimeField(read_only=True)
    # nested read-only list of content blocks (if prefetched)
    content_blocks = ContentBlockSerializer(many=True, read_only=True)

    class Meta:
        model = LessonVersion
        fields = ["id", "lesson", "version", "status", "author", "content", "change_summary", "created_at", "published_at", "content_blocks"]
        read_only_fields = ["id", "version", "created_at", "published_at", "content_blocks"]

    def to_domain(self) -> LessonVersionDomain:
        """
        For creation/updating of lesson versions.
        If instance exists, it's an update; for create, version will be assigned by domain/Service.
        """

        d = self.validated_data
        lesson = d.get("lesson")
        lesson_id = _maybe_pk_to_id(lesson)
        author = d.get("author")
        lv = LessonVersionDomain(
            lesson_id=lesson_id,
            version=d.get("version", 0) or 0,  # service will set real version on create
            status=d.get("status", "draft"),
            author_id=(author.id if author else None),
            content=d.get("content", {}),
            change_summary=d.get("change_summary")
        )
        # Validate content structure (this will validate content blocks payload)
        lv.validate_content()
        return lv

    @staticmethod
    def from_domain(domain: LessonVersionDomain) -> Dict[str, Any]:
        return domain.to_dict()


class LessonSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    module = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all(), source="module_id")
    title = serializers.CharField(max_length=255)
    position = serializers.IntegerField(default=0, min_value=0)
    content_type = serializers.ChoiceField(choices=[("lesson", "Lesson"), ("exploration", "Exploration"), ("exercise", "Exercise"), ("quiz", "Quiz")], default="lesson")
    published = serializers.BooleanField(default=False)
    versions = LessonVersionSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ["id", "module", "title", "position", "content_type", "published", "versions"]
        read_only_fields = ["id", "versions"]

    def to_domain(self) -> LessonDomain:
        d = self.validated_data
        module = d.get("module")
        lesson = LessonDomain(
            module_id=_maybe_pk_to_id(module),
            title=d["title"],
            position=d.get("position", 0),
            content_type=d.get("content_type", "lesson"),
            published=d.get("published", False)
        )
        lesson.validate()
        return lesson

    @staticmethod
    def from_domain(domain: LessonDomain) -> Dict[str, Any]:
        return domain.to_dict()


class SetStatusSerializer(serializers.Serializer):
    """
    Serializer này CHỈ dùng để validate đầu vào cho
    action 'set_status'.
    """
    # Lấy các choices từ LessonVersionDomain của bạn
    VALID_STATUSES = ("draft", "review", "published", "archived")
    
    status = serializers.ChoiceField(choices=VALID_STATUSES)


class ContentBlockInputSerializer(serializers.Serializer):
    """
    Serializer con, KHÔNG PHẢI ModelSerializer.
    Dùng để validate từng block trong danh sách 'content_blocks'
    khi client gửi lên.
    """
    # 'id' là Optional. 
    # - Nếu có (UUID), service sẽ hiểu là CẬP NHẬT.
    # - Nếu không có (None), service sẽ hiểu là TẠO MỚI.
    id = serializers.UUIDField(required=False, allow_null=True)
    
    # Lấy choices từ model ContentBlock
    TYPE_CHOICES = [
        ('text', ('Text')), ('image', ('Image')), ('video', ('Video')),
        ('quiz', ('Quiz')), ('exploration_ref', ('Exploration Reference'))
    ]
    type = serializers.ChoiceField(choices=TYPE_CHOICES)
    position = serializers.IntegerField(min_value=0)
    payload = serializers.JSONField(default=dict)

    # Không cần 'lesson_version' vì nó được lồng (nested)


class LessonVersionCreateSerializer(serializers.Serializer):
    """
    Serializer Input (Đầu vào) cho POST (Tạo mới) một Cụm LessonVersion.
    """
    change_summary = serializers.CharField(required=False, allow_blank=True)
    # Đây là nơi client gửi lên danh sách các block
    content_blocks = ContentBlockInputSerializer(many=True, required=False, default=[])
    

class LessonVersionUpdateSerializer(serializers.Serializer):
    """
    Serializer Input (Đầu vào) cho PATCH (Cập nhật) một Cụm LessonVersion.
    Tất cả các trường đều là 'required=False'.
    """
    change_summary = serializers.CharField(required=False, allow_blank=True)
    
    # 'content_blocks' cũng là optional.
    # Nếu client không gửi key này, service sẽ không đụng đến blocks.
    # Nếu client gửi key này (kể cả list rỗng), service sẽ "Sync" theo list đó.
    content_blocks = ContentBlockInputSerializer(many=True, required=False)


class ExplorationStateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    exploration = serializers.PrimaryKeyRelatedField(queryset=Exploration.objects.all(), source="exploration_id")
    name = serializers.CharField(max_length=255)
    content = serializers.JSONField()
    interaction = serializers.JSONField()

    class Meta:
        model = ExplorationState
        fields = ["id", "exploration", "name", "content", "interaction"]
        read_only_fields = ["id"]

    def to_domain(self) -> ExplorationStateDomain:
        d = self.validated_data
        exploration = d.get("exploration")
        state = ExplorationStateDomain(
            exploration_id=_maybe_pk_to_id(exploration),
            name=d["name"],
            content=d.get("content", {}),
            interaction=d.get("interaction", {})
        )
        state.validate()
        return state

    @staticmethod
    def from_domain(domain: ExplorationStateDomain) -> Dict[str, Any]:
        return domain.to_dict()


class ExplorationTransitionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    exploration = serializers.PrimaryKeyRelatedField(queryset=Exploration.objects.all(), source="exploration_id")
    from_state = serializers.PrimaryKeyRelatedField(queryset=ExplorationState.objects.all())
    to_state = serializers.PrimaryKeyRelatedField(queryset=ExplorationState.objects.all())
    condition = serializers.JSONField()

    class Meta:
        model = ExplorationTransition
        fields = ["id", "exploration", "from_state", "to_state", "condition"]
        read_only_fields = ["id"]

    def to_domain(self) -> ExplorationTransitionDomain:
        d = self.validated_data
        exploration = d.get("exploration")
        from_state = d.get("from_state")
        to_state = d.get("to_state")
        t = ExplorationTransitionDomain(
            exploration_id=_maybe_pk_to_id(exploration),
            from_state=(_maybe_pk_to_id(from_state) if from_state else d.get("from_state")),
            to_state=(_maybe_pk_to_id(to_state) if to_state else d.get("to_state")),
            condition=d.get("condition", {})
        )
        t.validate()
        return t

    @staticmethod
    def from_domain(domain: ExplorationTransitionDomain) -> Dict[str, Any]:
        return domain.to_dict()


class ExplorationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(max_length=255)
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True, required=False)
    language = serializers.CharField(max_length=8, default="vi")
    initial_state_name = serializers.CharField(max_length=255, allow_null=True, required=False)
    schema_version = serializers.IntegerField(default=1)
    published = serializers.BooleanField(default=False)
    states = ExplorationStateSerializer(many=True, read_only=True)
    transitions = ExplorationTransitionSerializer(many=True, read_only=True)

    class Meta:
        model = Exploration
        fields = ["id", "title", "owner", "language", "initial_state_name", "schema_version", "published", "states", "transitions"]
        read_only_fields = ["id", "states", "transitions"]

    def to_domain(self) -> ExplorationDomain:
        d = self.validated_data
        owner = d.get("owner")
        exp = ExplorationDomain(
            title=d["title"],
            owner_id=(owner.id if owner else None),
            language=d.get("language", "vi"),
            initial_state_name=d.get("initial_state_name"),
            schema_version=d.get("schema_version", 1),
            published=d.get("published", False)
        )
        exp.validate()
        return exp

    @staticmethod
    def from_domain(domain: ExplorationDomain) -> Dict[str, Any]:
        return domain.to_dict()


# ---------------------------------
# Full Read Serializers for nesting
# ---------------------------------

class LessonReadSerializer(LessonSerializer):
    """Read-only serializer for a lesson, with nested versions."""
    versions = LessonVersionSerializer(many=True, read_only=True)

    class Meta(LessonSerializer.Meta):
        fields = LessonSerializer.Meta.fields + ['versions']


class ModuleReadSerializer(ModuleSerializer):
    """Read-only serializer for a module, with nested lessons."""
    lessons = LessonReadSerializer(many=True, read_only=True)

    class Meta(ModuleSerializer.Meta):
        fields = ModuleSerializer.Meta.fields + ['lessons']


class CourseDetailReadSerializer(CourseSerializer):
    """Read-only serializer for a course, with nested modules."""
    modules = ModuleReadSerializer(many=True, read_only=True)
    subject = SubjectSerializer(read_only=True)

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ['modules']


class LessonVersionReadSerializer(LessonVersionSerializer):
    """Read-only serializer for a lesson version, with content blocks."""
    content_blocks = ContentBlockSerializer(many=True, read_only=True)

    class Meta(LessonVersionSerializer.Meta):
        fields = LessonVersionSerializer.Meta.fields + ['content_blocks']


# ---------------------------------
# Full Exploration Serializer
# ---------------------------------

class RuleSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleSpec,
        fields = ['rule_type', 'inputs_json']

class AnswerGroupSerializer(serializers.ModelSerializer):
    rule_specs = RuleSpecSerializer(many=True, read_only=True)
    class Meta:
        model = AnswerGroup
        exclude = ['id', 'state']

class HintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hint
        fields = ['hint_html']

class SolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solution
        exclude = ['state']

class FullExplorationStateSerializer(serializers.ModelSerializer):
    """Serializer for a single State within an Exploration, including all details."""
    customization_args = serializers.JSONField(source='get_customization_args_json')
    hints = HintSerializer(many=True, read_only=True)
    answer_groups = AnswerGroupSerializer(many=True, read_only=True)
    solution = SolutionSerializer(read_only=True)

    class Meta:
        model = ExplorationState
        fields = [
            'name', 'content_html', 'classifier_model_id', 'interaction_id',
            'card_is_checkpoint', 'customization_args', 'hints', 'answer_groups', 'solution'
        ]

    def get_customization_args_json(self, obj):
        # This method converts the related InteractionCustomizationArg objects into the expected JSON structure
        args = {}
        for arg in obj.customization_args.all():
            args[arg.arg_name] = arg.arg_value_json
        return args

class FullExplorationSerializer(serializers.ModelSerializer):
    """
    The "giant JSON" serializer for GETting an entire exploration for the editor/player.
    """
    states = serializers.SerializerMethodField()
    param_specs = serializers.JSONField()
    param_changes = serializers.JSONField()
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Exploration
        fields = [
            'id', 'title', 'objective', 'language', 'category', 'tags',
            'blurb', 'author_notes', 'published', 'init_state_name',
            'param_specs', 'param_changes', 'states'
        ]

    def get_states(self, obj):
        # Use a dictionary for states, with state names as keys, as is common in Oppia.
        states_dict = {}
        for state in obj.states.prefetch_related('hints', 'answer_groups__rule_specs', 'solution', 'customization_args').all():
            states_dict[state.name] = FullExplorationStateSerializer(state).data
        return states_dict


# -----------------------
# Command / Input-only Serializers (to produce Domain Command objects)
# -----------------------
# These are used by endpoints for create/publish actions and convert to domain commands

class CreateCourseInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    subject_id = serializers.UUIDField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    grade = serializers.CharField(max_length=16, required=False, allow_blank=True)
    owner_id = serializers.IntegerField(required=False, allow_null=True) # Assuming user ID is int

    def to_domain(self):
        from content.domains.commands import CreateCourseCommand
        d = self.validated_data
        return CreateCourseCommand(
            title=d['title'],
            subject_id=str(d['subject_id']) if d.get('subject_id') else None,
            description=d.get('description'),
            grade=d.get('grade'),
            owner_id=d.get('owner_id')
        )

class AddModuleInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    position = serializers.IntegerField(required=False, min_value=0)

    def to_domain(self, course_id: str):
        from content.domains.commands import AddModuleCommand
        d = self.validated_data
        return AddModuleCommand(
            course_id=course_id,
            title=d['title'],
            position=d.get('position')
        )

class CreateLessonInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    position = serializers.IntegerField(required=False, min_value=0)
    content_type = serializers.ChoiceField(choices=LessonDomain.VALID_CONTENT_TYPES, default='lesson')

    def to_domain(self, module_id: str):
        from content.domains.commands import CreateLessonCommand
        d = self.validated_data
        return CreateLessonCommand(
            module_id=module_id,
            title=d['title'],
            position=d.get('position'),
            content_type=d.get('content_type')
        )

class CreateLessonVersionInputSerializer(serializers.Serializer):
    author_id = serializers.IntegerField(required=False, allow_null=True)
    content = serializers.JSONField()
    change_summary = serializers.CharField(required=False, allow_blank=True)

    def to_domain(self, lesson_id: str):
        from content.domains.commands import CreateLessonVersionCommand
        d = self.validated_data
        return CreateLessonVersionCommand(
            lesson_id=lesson_id,
            author_id=d.get('author_id'),
            content=d['content'],
            change_summary=d.get('change_summary')
        )

class PublishLessonVersionInputSerializer(serializers.Serializer):
    version = serializers.IntegerField(min_value=1)
    publish_comment = serializers.CharField(required=False, allow_blank=True)

    def to_domain(self, lesson_id: str):
        from content.domains.commands import PublishLessonVersionCommand
        d = self.validated_data
        return PublishLessonVersionCommand(
            lesson_id=lesson_id,
            version=d['version'],
            publish_comment=d.get('publish_comment')
        )

class AddContentBlockInputSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=ContentBlockDomain.VALID_TYPES)
    position = serializers.IntegerField(required=False, min_value=0)
    payload = serializers.JSONField()

    def to_domain(self, lesson_version_id: str):
        from content.domains.commands import AddContentBlockCommand
        d = self.validated_data
        return AddContentBlockCommand(
            lesson_version_id=lesson_version_id,
            type=d['type'],
            position=d.get('position'),
            payload=d['payload']
        )

class CreateExplorationInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    owner_id = serializers.IntegerField(required=False, allow_null=True)
    language = serializers.CharField(max_length=8, default='vi')

    def to_domain(self):
        from content.domains.commands import CreateExplorationCommand
        d = self.validated_data
        return CreateExplorationCommand(
            title=d['title'],
            owner_id=d.get('owner_id'),
            language=d.get('language')
        )

class AddExplorationStateInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    content = serializers.JSONField()
    interaction = serializers.JSONField()

    def to_domain(self, exploration_id: str):
        from content.domains.commands import AddExplorationStateCommand
        d = self.validated_data
        return AddExplorationStateCommand(
            exploration_id=exploration_id,
            name=d['name'],
            content=d['content'],
            interaction=d['interaction']
        )

class AddExplorationTransitionInputSerializer(serializers.Serializer):
    from_state = serializers.CharField(max_length=255)
    to_state = serializers.CharField(max_length=255)
    condition = serializers.JSONField()

    def to_domain(self, exploration_id: str):
        from content.domains.commands import AddExplorationTransitionCommand
        d = self.validated_data
        return AddExplorationTransitionCommand(
            exploration_id=exploration_id,
            from_state=d['from_state'],
            to_state=d['to_state'],
            condition=d['condition']
        )

class ChangeVersionStatusInputSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=LessonVersionDomain.VALID_STATUSES)

    def to_domain(self) -> ChangeVersionStatusCommand:
        return ChangeVersionStatusCommand(status=self.validated_data['status'])

class ReorderItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    position = serializers.IntegerField()

class ReorderItemsInputSerializer(serializers.Serializer):
    items = ReorderItemSerializer(many=True)

    def to_domain(self, reorder_type: str):
        order_map = {item['id']: item['position'] for item in self.validated_data['items']}
        if reorder_type == 'modules':
            return ReorderModulesCommand(order_map=order_map)
        if reorder_type == 'lessons':
            return ReorderLessonsCommand(order_map=order_map)
        if reorder_type == 'blocks':
            return ReorderContentBlocksCommand(order_map=order_map)
        raise ValueError("Invalid reorder type")
