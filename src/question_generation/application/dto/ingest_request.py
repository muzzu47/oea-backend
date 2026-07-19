from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class IngestRequest:
    source_text: str
    subject_name: str
    chapter_name: str
    concept_names: List[str] = field(default_factory=list[str])