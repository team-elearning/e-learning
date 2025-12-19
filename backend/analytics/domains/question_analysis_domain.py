from dataclasses import dataclass
from typing import List, Dict, Optional



@dataclass
class QuestionAnalysisDomain:
    """Kết quả phân tích cho TỪNG câu hỏi"""
    question_id: str
    prompt_text: str
    question_type: str
    
    total_attempts: int
    correct_ratio: float      # Difficulty Index (0-100%)
    discrimination_index: float # Độ phân biệt (-1.0 đến +1.0)
    
    # Phân tích đáp án nhiễu (Distractors)
    # Ví dụ: {'A': 10%, 'B': 80% (Đúng), 'C': 5%, 'D': 5%}
    option_distribution: Dict[str, float] 
    
    status: str               # 'good', 'too_easy', 'too_hard', 'check_key'
    recommendation: str       # Lời khuyên của AI