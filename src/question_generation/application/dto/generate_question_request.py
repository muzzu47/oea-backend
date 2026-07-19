from dataclasses import dataclass, field
from typing import List

@dataclass(slots=True)
class GenerateQuestionRequest:
    subject: str
    chapters: List[str] = field(default_factory=list[str])
    concepts: List[str] = field(default_factory=list[str])
    difficulty: str = "medium"
    count: int = 1