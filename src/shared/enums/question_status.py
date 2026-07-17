from enum import Enum


class QuestionStatus(str, Enum):
    """
    Represents the lifecycle state of a question.
    """

    GENERATED = "generated"
    VALIDATED = "validated"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"