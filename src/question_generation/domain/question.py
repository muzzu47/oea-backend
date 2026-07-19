from dataclasses import dataclass, field
from typing import List

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
    generated_date: str = ""
    generated_by: str = "ai"
    validation_status: str = "generated"
    validator_remarks: str = ""