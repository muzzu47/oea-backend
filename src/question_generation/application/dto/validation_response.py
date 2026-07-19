from dataclasses import dataclass


@dataclass(slots=True)
class ValidationResponse:
    is_valid: bool
    remarks: str = ""