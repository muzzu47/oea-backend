from question_generation.domain.question import Question
from question_generation.question_validation.validator_result import ValidatorResult
from question_generation.question_validation.option_validator import OptionValidator
from question_generation.question_validation.explanation_validator import ExplanationValidator
from question_generation.question_validation.duplicate_validator import DuplicateValidator
from question_generation.question_validation.bloom_validator import BloomValidator
from question_generation.question_validation.difficulty_validator import DifficultyValidator

class QuestionValidationService:
    """
    Service responsible for orchestrating the multi-tier validation pipeline.
    Runs Tier 1 (cheap, fast heuristics) first, and only runs Tier 2 (paid, slow AI audits)
    if the question is structurally valid and non-duplicate.
    """

    def __init__(
        self,
        option_validator: OptionValidator,
        explanation_validator: ExplanationValidator,
        duplicate_validator: DuplicateValidator,
        bloom_validator: BloomValidator,
        difficulty_validator: DifficultyValidator
    ):
        self.option_validator = option_validator
        self.explanation_validator = explanation_validator
        self.duplicate_validator = duplicate_validator
        self.bloom_validator = bloom_validator
        self.difficulty_validator = difficulty_validator

    def validate_question(self, question: Question) -> ValidatorResult:
        """
        Orchestrates validation checks for a single question.
        Returns a ValidatorResult describing the outcome and reason.
        """
        # --- TIER 1: Heuristic Structural Validation (Fast & Free) ---
        
        # 1. Check Option Structure
        opt_res = self.option_validator.validate(question)
        if not opt_res.is_valid:
            return opt_res

        # 2. Check Explanation Depth
        exp_res = self.explanation_validator.validate(question)
        if not exp_res.is_valid:
            return exp_res

        # 3. Check Duplicate Vector Similarity
        dup_res = self.duplicate_validator.validate(question)
        if not dup_res.is_valid:
            return dup_res

        # --- TIER 2: AI Psychometric Audit (Paid & Slow) ---
        
        # 4. Check Cognitive Bloom's level alignment
        bloom_res = self.bloom_validator.validate(question)
        if not bloom_res.is_valid:
            return bloom_res

        # 5. Check actual question difficulty
        diff_res = self.difficulty_validator.validate(question)
        if not diff_res.is_valid:
            return diff_res

        # If all checks pass, the question is marked as validated
        return ValidatorResult(is_valid=True, remarks="All validation checks passed.")
