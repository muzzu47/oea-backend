from enum import Enum

class DifficultyLevel(str, Enum):
    """
    Represents the difficulty level of a question.

    This enum is shared across Question Generation,
    CBT, and Evaluation modules.
    """

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"