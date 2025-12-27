from dataclasses import dataclass
from typing import List
from uuid import UUID


@dataclass
class BlockSyllabusDomain:
    id: UUID
    title: str
    type: str
    is_completed: bool
    is_locked: bool # Logic mở khóa tuần tự
    duration: int # Metadata hiển thị (VD: 10 phút)


@dataclass
class LessonSyllabusDomain:
    id: UUID
    title: str
    is_completed: bool
    is_locked: bool
    blocks: List[BlockSyllabusDomain]


@dataclass
class ModuleSyllabusDomain:
    id: UUID
    title: str
    is_completed: bool
    lessons: List[LessonSyllabusDomain]


@dataclass
class CourseSyllabusDomain:
    course_id: UUID
    percent_completed: float
    modules: List[ModuleSyllabusDomain]