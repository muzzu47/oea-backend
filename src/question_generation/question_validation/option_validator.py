from question_generation.domain.question import Question
from question_generation.question_validation.validator_result import ValidatorResult

class OptionValidator:
    """
    Tier 1 Heuristic Validator.
    Verifies multiple-choice option structure, limits, duplication, and correctness.
    """

    def validate(self, question: Question) -> ValidatorResult:
        options = question.options

        # Rule 1: Must have exactly 4 options
        if len(options) != 4:
            return ValidatorResult(
                is_valid=False,
                remarks=f"Invalid option count. Expected 4, got {len(options)}."
            )

        # Rule 2: Options must be non-empty strings
        for idx, opt in enumerate(options):
            if not opt or not str(opt).strip():
                return ValidatorResult(
                    is_valid=False,
                    remarks=f"Option at index {idx} is empty or whitespace."
                )

        # Rule 3: Correct answer must match one of the 4 options exactly
        if question.correct_answer not in options:
            return ValidatorResult(
                is_valid=False,
                remarks="Correct answer does not match any of the provided options."
            )

        # Rule 4: Options must be unique (no duplicates)
        # Convert all to lowercase strips to detect near-duplicates (e.g. "gravity" vs "Gravity")
        normalized_options = {opt.strip().lower() for opt in options}
        if len(normalized_options) != 4:
            return ValidatorResult(
                is_valid=False,
                remarks="Duplicate multiple-choice options detected."
            )

        return ValidatorResult(is_valid=True)
