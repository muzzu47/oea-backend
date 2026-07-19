from dataclasses import dataclass, field
from typing import List

@dataclass(slots=True)
class GenerateQuestionResponse:
    questions: List[object] = field(default_factory=list[object])