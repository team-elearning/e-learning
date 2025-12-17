from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID



class AIRecommendationInput(BaseModel):
    """Input cho việc search/suggest"""
    q: str = Field(..., min_length=1)
    top_n: int = Field(default=5, ge=1, le=20)