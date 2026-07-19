from dataclasses import dataclass, field
from typing import List

@dataclass(slots=True)
class Chapter:
    name: str
    subject_name: str
    concepts: List[str] = field(default_factory=list[str])