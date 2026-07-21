from dataclasses import dataclass, field
from typing import List, Optional

@dataclass(slots=True)
class Question:
    subject: str
    chapter: str
    topic: str
    concept: str
    topic_weightage: str
    question: str
    options: List[str] = field(default_factory=list[str])
    correct_answer: str = ""
    solution: str = ""
    difficulty_level: str = "medium"
    question_type: str = "single_correct"
    exam_type: Optional[str] = None
    generated_date: str = ""
    generated_by: str = "ai"
    validation_status: str = "generated"
    validator_remarks: str = ""
    source_chunk_id: Optional[int] = None
    is_active: bool = True
    usage_count: int = 0
    embedding: Optional[List[float]] = None
