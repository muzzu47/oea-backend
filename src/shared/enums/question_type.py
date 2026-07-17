from enum import Enum


class QuestionType(str, Enum):
    """
    Represents the type of a question.
    """

    SINGLE_CORRECT = "single_correct"
    MULTIPLE_CORRECT = "multiple_correct"
    NUMERICAL = "numerical"