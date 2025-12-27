from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict



# --- LEVEL 4: BLOCK ---
class BlockSyllabusOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: Optional[str]
    type: str
    is_completed: bool
    is_locked: bool
    duration: int = 0


# --- LEVEL 3: LESSON ---
class LessonSyllabusOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    is_completed: bool
    is_locked: bool
    blocks: List[BlockSyllabusOutput] = []


# --- LEVEL 2: MODULE ---
class ModuleSyllabusOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    is_completed: bool
    lessons: List[LessonSyllabusOutput] = []


# --- LEVEL 1: COURSE (ROOT) ---
class CourseSyllabusOutput(BaseModel):
    """
    DTO trả về cấu trúc khóa học kèm tiến độ.
    Dùng cho màn hình "Học" (Learning Dashboard).
    """
    model_config = ConfigDict(from_attributes=True)

    course_id: UUID
    percent_completed: float
    modules: List[ModuleSyllabusOutput] = []