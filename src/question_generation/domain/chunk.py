from dataclasses import dataclass, field
from typing import List, Optional

@dataclass(slots=True)
class Chunk:
    """
    Represents a specific chunk of text extracted from a textbook.
    Used for vector indexing and semantic search context retrieval.
    """
    textbook_title: str
    subject_name: str
    chapter_name: str
    content: str
    page_number: int
    chunk_index: int
    concept_name: Optional[str] = None
    exam_type: Optional[str] = None
    embedding: List[float] = field(default_factory=list[float])
