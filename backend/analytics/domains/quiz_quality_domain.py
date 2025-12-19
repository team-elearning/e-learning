from dataclasses import dataclass
from typing import List, Dict, Optional

from analytics.domains.question_analysis_domain import QuestionAnalysisDomain



@dataclass
class QuizQualityDomain:
    """Báo cáo tổng quan cho cả bài thi"""
    quiz_id: str
    quiz_title: str
    total_attempts: int
    average_score: float
    
    questions: List[QuestionAnalysisDomain]