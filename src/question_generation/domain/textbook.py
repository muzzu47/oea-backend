from dataclasses import dataclass, field
from typing import List, Optional

@dataclass(slots=True)
class Textbook:
    """
    Represents the metadata of an uploaded or registered textbook.
    """
    title: str
    subject_name: str
    file_path: str
    author: Optional[str] = None
    exam_type: Optional[str] = None
    chapters: List[str] = field(default_factory=list[str])
