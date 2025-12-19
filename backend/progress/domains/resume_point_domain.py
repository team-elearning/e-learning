from dataclasses import dataclass
from datetime import datetime
from typing import Optional



@dataclass
class ResumePointDomain:
    """Nút bấm 'Học tiếp' hoặc 'Bắt đầu'"""
    block_id: str
    lesson_title: str
    block_type: str
    is_start: bool = False