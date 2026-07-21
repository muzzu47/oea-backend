from question_generation.domain.question import Question
from question_generation.question_validation.validator_result import ValidatorResult

class ExplanationValidator:
    """
    Tier 1 Heuristic Validator.
    Verifies that the question solution/explanation is non-empty and sufficiently detailed.
    """

    def __init__(self, min_length: int = 20):
        self.min_length = min_length

    def validate(self, question: Question) -> ValidatorResult:
        solution = question.solution

        # Rule 1: Solution must exist and be non-empty
        if not solution or not str(solution).strip():
            return ValidatorResult(
                is_valid=False,
                remarks="Solution/explanation is missing or empty."
            )

        # Rule 2: Solution must meet the minimum descriptive length
        cleaned_solution = solution.strip()
        if len(cleaned_solution) < self.min_length:
            return ValidatorResult(
                is_valid=False,
                remarks=(
                    f"Solution explanation is too short ({len(cleaned_solution)} chars). "
                    f"Expected at least {self.min_length} characters to guarantee quality."
                )
            )

        return ValidatorResult(is_valid=True)
