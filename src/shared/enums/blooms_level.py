from enum import Enum


class BloomsLevel(str, Enum):
    """
    Represents Bloom's Taxonomy cognitive levels.
    """

    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"