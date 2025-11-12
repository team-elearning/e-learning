import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from content.services.exceptions import DomainValidationError

# -----------------------
# Subject Commands
# -----------------------

@dataclass
class CreateSubjectCommand:
    title: str
    slug: str

    def validate(self):
        if not self.title or not self.title.strip():
            raise DomainValidationError("Subject title required.")
        if not self.slug or " " in self.slug:
            raise DomainValidationError("Subject slug required and cannot contain spaces.")

@dataclass
class UpdateSubjectCommand:
    title: Optional[str] = None
    slug: Optional[str] = None

    def validate(self):
        if not self.title and not self.slug:
            raise DomainValidationError("At least one field (title, slug) must be provided for update.")

# -----------------------
# Course Commands
# -----------------------

@dataclass
class CreateCourseCommand:
    title: str
    subject_id: Optional[str] = None
    description: Optional[str] = None
    grade: Optional[str] = None
    owner_id: Optional[int] = None
    slug: Optional[str] = None

    def validate(self):
        if not self.title or not self.title.strip():
            raise DomainValidationError("Course title is required.")
        if self.slug and (" " in self.slug or len(self.slug) < 2):
            raise DomainValidationError("Slug must be at least 2 chars and contain no spaces.")
        if self.grade and len(str(self.grade)) > 16:
            raise DomainValidationError("Invalid grade length.")

@dataclass
class UpdateCourseCommand:
    title: Optional[str] = None
    description: Optional[str] = None
    grade: Optional[str] = None

    def validate(self):
        # No complex validation, empty update is acceptable
        pass

@dataclass
class PublishCourseCommand:
    published: bool
    require_all_lessons_published: bool = False

    def validate(self):
        pass

@dataclass
class AssignCourseOwnerCommand:
    owner_id: int

    def validate(self):
        if not self.owner_id:
            raise DomainValidationError("owner_id is required.")

# -----------------------
# Module Commands
# -----------------------

@dataclass
class AddModuleCommand:
    course_id: str
    title: str
    position: Optional[int] = None

    def validate(self):
        if not self.course_id:
            raise DomainValidationError("course_id required.")
        if not self.title or not self.title.strip():
            raise DomainValidationError("module title required.")

@dataclass
class UpdateModuleCommand:
    title: Optional[str] = None
    position: Optional[int] = None

    def validate(self):
        pass

@dataclass
class ReorderModulesCommand:
    order_map: Dict[str, int]

    def validate(self):
        if not isinstance(self.order_map, dict):
            raise DomainValidationError("order_map must be a dictionary.")

# -----------------------
# Lesson Commands
# -----------------------

@dataclass
class CreateLessonCommand:
    module_id: str
    title: str
    content_type: str = "lesson"
    position: Optional[int] = None

    def validate(self):
        if not self.module_id:
            raise DomainValidationError("module_id required.")
        if not self.title or not self.title.strip():
            raise DomainValidationError("lesson title required.")
        if self.content_type not in ("lesson", "exploration", "exercise", "quiz"):
            raise DomainValidationError("Invalid content_type.")

@dataclass
class UpdateLessonCommand:
    title: Optional[str] = None
    position: Optional[int] = None
    content_type: Optional[str] = None

    def validate(self):
        pass

@dataclass
class PublishLessonCommand:
    published: bool

    def validate(self):
        pass

@dataclass
class ReorderLessonsCommand:
    order_map: Dict[str, int]

    def validate(self):
        if not isinstance(self.order_map, dict):
            raise DomainValidationError("order_map must be a dictionary.")

# -----------------------
# Lesson Version Commands
# -----------------------

@dataclass
class CreateLessonVersionCommand:
    lesson_id: str
    author_id: Optional[int]
    content: Dict[str, Any]
    change_summary: Optional[str] = None

    def validate(self):
        if not self.lesson_id:
            raise DomainValidationError("lesson_id required.")
        if not isinstance(self.content, dict) or not self.content:
            raise DomainValidationError("content must be a non-empty object/dict.")

@dataclass
class UpdateLessonVersionCommand:
    content: Dict[str, Any]

    def validate(self):
        if not isinstance(self.content, dict):
            raise DomainValidationError("content must be a dictionary.")

@dataclass
class ChangeVersionStatusCommand:
    status: str

    def validate(self):
        if self.status not in ("draft", "review", "published", "archived"):
            raise DomainValidationError("Invalid status.")

@dataclass
class PublishLessonVersionCommand:
    lesson_id: str
    version: int
    publish_comment: Optional[str] = None

    def validate(self):
        if not self.lesson_id:
            raise DomainValidationError("lesson_id required.")
        if not isinstance(self.version, int) or self.version < 1:
            raise DomainValidationError("version must be integer >= 1.")

# -----------------------
# Content Block Commands
# -----------------------

@dataclass
class AddContentBlockCommand:
    lesson_version_id: str
    type: str
    position: Optional[int]
    payload: Dict[str, Any]

    def validate(self):
        if not self.lesson_version_id:
            raise DomainValidationError("lesson_version_id required.")
        if self.type not in ("text", "image", "video", "quiz", "exploration_ref"):
            raise DomainValidationError("Invalid content block type.")
        if not isinstance(self.payload, dict):
            raise DomainValidationError("payload must be dict.")

@dataclass
class UpdateContentBlockCommand:
    type: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    position: Optional[int] = None

    def validate(self):
        pass

@dataclass
class ReorderContentBlocksCommand:
    order_map: Dict[str, int]

    def validate(self):
        if not isinstance(self.order_map, dict):
            raise DomainValidationError("order_map must be a dictionary.")

# -----------------------
# Exploration Commands
# -----------------------

@dataclass
class CreateExplorationCommand:
    title: str
    owner_id: Optional[int]
    language: str = "vi"
    initial_state_name: Optional[str] = None
    schema_version: int = 1

    def validate(self):
        if not self.title or not self.title.strip():
            raise DomainValidationError("Exploration title required.")
        if not isinstance(self.schema_version, int) or self.schema_version < 1:
            raise DomainValidationError("schema_version must be >=1.")

@dataclass
class UpdateExplorationCommand:
    title: Optional[str] = None
    language: Optional[str] = None

    def validate(self):
        pass

@dataclass
class PublishExplorationCommand:
    published: bool

    def validate(self):
        pass

@dataclass
class AddExplorationStateCommand:
    exploration_id: str
    name: str
    content: Dict[str, Any]
    interaction: Dict[str, Any]

    def validate(self):
        if not self.exploration_id:
            raise DomainValidationError("exploration_id required.")
        if not self.name or not self.name.strip():
            raise DomainValidationError("state name required.")
        if not isinstance(self.content, dict) or not isinstance(self.interaction, dict):
            raise DomainValidationError("content and interaction must be dicts.")

@dataclass
class UpdateExplorationStateCommand:
    name: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    interaction: Optional[Dict[str, Any]] = None

    def validate(self):
        pass

@dataclass
class AddExplorationTransitionCommand:
    exploration_id: str
    from_state: str
    to_state: str
    condition: Dict[str, Any]

    def validate(self):
        if not self.exploration_id:
            raise DomainValidationError("exploration_id required.")
        if not self.from_state or not self.to_state:
            raise DomainValidationError("from_state and to_state required.")
        if not isinstance(self.condition, dict):
            raise DomainValidationError("condition must be dict.")