from dataclasses import dataclass



@dataclass
class AnalyticsJobResultDomain:
    course_id: str
    total_students: int
    processed_count: int
    status: str      # 'success', 'failed'
    execution_time: float # giây