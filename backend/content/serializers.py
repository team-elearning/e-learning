# content/serializers.py
from typing import Any, Dict, List, Optional
from django.contrib.auth import get_user_model
from rest_framework import serializers

from content import models
from content.domains.subject_domain import SubjectDomain
from content.domains.course_domain import CourseDomain
from content.domains.module_domain import ModuleDomain
from content.domains.lesson_domain import LessonDomain
from content.domains.lesson_version_domain import LessonVersionDomain
from content.domains.content_block_domain import ContentBlockDomain
from content.domains.exploration_domain import ExplorationDomain, ExplorationTransitionDomain, ExplorationStateDomain
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

class SubjectSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=255)

    class Meta:
        model = models.Subject
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
    subject = serializers.PrimaryKeyRelatedField(queryset=models.Subject.objects.all(), allow_null=True, required=False)
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True, required=False)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True, required=False)
    grade = serializers.CharField(max_length=16, allow_blank=True, required=False)
    slug = serializers.SlugField(max_length=255, required=False, allow_null=True)
    published = serializers.BooleanField(default=False)
    published_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = models.Course
        fields = ["id", "subject", "title", "description", "grade", "owner", "slug", "published", "published_at"]
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
    id = serializers.UUIDField(read_only=True)
    course = serializers.PrimaryKeyRelatedField(queryset=models.Course.objects.all())
    title = serializers.CharField(max_length=255)
    position = serializers.IntegerField(default=0, min_value=0)

    class Meta:
        model = models.Module
        fields = ["id", "course", "title", "position"]
        read_only_fields = ["id"]

    def to_domain(self) -> ModuleDomain:
        d = self.validated_data
        domain = ModuleDomain(
            course_id=_maybe_pk_to_id(d["course"]),
            title=d["title"],
            position=d.get("position", 0)
        )
        domain.validate()
        return domain

    @staticmethod
    def from_domain(domain: ModuleDomain) -> Dict[str, Any]:
        return domain.to_dict()


class ContentBlockSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    lesson_version = serializers.PrimaryKeyRelatedField(queryset=models.LessonVersion.objects.all(), source="lesson_version_id")
    type = serializers.ChoiceField(choices=[("text", "Text"), ("image", "Image"), ("video", "Video"), ("quiz", "Quiz"), ("exploration_ref", "ExplorationRef")])
    position = serializers.IntegerField(default=0, min_value=0)
    payload = serializers.JSONField()

    class Meta:
        model = models.ContentBlock
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


class LessonVersionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    lesson = serializers.PrimaryKeyRelatedField(queryset=models.Lesson.objects.all(), source="lesson_id")
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
        model = models.LessonVersion
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
    module = serializers.PrimaryKeyRelatedField(queryset=models.Module.objects.all(), source="module_id")
    title = serializers.CharField(max_length=255)
    position = serializers.IntegerField(default=0, min_value=0)
    content_type = serializers.ChoiceField(choices=[("lesson", "Lesson"), ("exploration", "Exploration"), ("exercise", "Exercise"), ("quiz", "Quiz")], default="lesson")
    published = serializers.BooleanField(default=False)
    versions = LessonVersionSerializer(many=True, read_only=True)

    class Meta:
        model = models.Lesson
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


class ExplorationStateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    exploration = serializers.PrimaryKeyRelatedField(queryset=models.Exploration.objects.all(), source="exploration_id")
    name = serializers.CharField(max_length=255)
    content = serializers.JSONField()
    interaction = serializers.JSONField()

    class Meta:
        model = models.ExplorationState
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
    exploration = serializers.PrimaryKeyRelatedField(queryset=models.Exploration.objects.all(), source="exploration_id")
    from_state = serializers.PrimaryKeyRelatedField(queryset=models.ExplorationState.objects.all())
    to_state = serializers.PrimaryKeyRelatedField(queryset=models.ExplorationState.objects.all())
    condition = serializers.JSONField()

    class Meta:
        model = models.ExplorationTransition
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
        model = models.Exploration
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


# -----------------------
# Command / Input-only Serializers (to produce Domain Command objects)
# -----------------------
# These are used by endpoints for create/publish actions and convert to d
