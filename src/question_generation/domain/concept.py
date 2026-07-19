from dataclasses import dataclass


@dataclass(slots=True)
class Concept:
    name: str
    chapter_name: str
    weightage: str = "normal"