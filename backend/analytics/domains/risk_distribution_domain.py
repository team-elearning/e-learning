from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any



@dataclass
class RiskDistributionDomain:
    """Domain con: Phân bố rủi ro (Dùng vẽ Pie Chart)"""
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0
    
    @property
    def total(self):
        return self.low + self.medium + self.high + self.critical