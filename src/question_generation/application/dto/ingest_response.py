from dataclasses import dataclass, field
from typing import List

@dataclass(slots=True)
class IngestResponse:
    subject: object
    chapter: object
    concepts: List[object] = field(default_factory=list[object])