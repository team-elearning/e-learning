from dataclasses import dataclass
from typing import List, Dict

from assignments.domain.value_objects.rubric_criterion import RubricCriterion



@dataclass(frozen=True)
class Rubric:
    """Composite value object representing grading rubric.
    The `weights` map criterion.id -> weight in [0,1]. The sum may be <= 1.
    """
    criteria: List[RubricCriterion]
    weights: Dict[str, float]  # criterion_id -> weight (0..1)

    def __post_init__(self):
        ids = {c.id for c in self.criteria}
        if set(self.weights.keys()) - ids:
            raise ValueError("Weights refer to unknown criterion id(s).")
        for w in self.weights.values():
            if not (0.0 <= w <= 1.0):
                raise ValueError("Each weight must be between 0 and 1.")