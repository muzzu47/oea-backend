from dataclasses import dataclass

@dataclass(slots=True)
class ValidatorResult:
    """
    Represents the result of a single question validation rule check.
    """
    is_valid: bool
    remarks: str = ""
