import json
import re
from typing import Optional

from question_generation.application.interfaces.llm_provider import LlmProvider
from question_generation.domain.question import Question
from question_generation.question_validation.validator_result import ValidatorResult

class DifficultyValidator:
    """
    Tier 2 AI Auditor.
    Prompts the LLM to audit the question's actual difficulty level
    to ensure it matches the target difficulty tier (easy, medium, hard).
    """

    def __init__(self, llm_provider: LlmProvider):
        self.llm_provider = llm_provider

    def validate(self, question: Question) -> ValidatorResult:
        # Prompt Gemini to audit the actual difficulty level
        prompt = f"""
Analyze the following multiple-choice question and evaluate its difficulty level for the exam standard.

Question:
{question.question}

Options:
{question.options}

Correct Answer:
{question.correct_answer}

Explanation:
{question.solution}

Select exactly one of these difficulty levels:
- easy
- medium
- hard

You MUST respond ONLY with a JSON object in this format:
{{
  "difficulty_level": "one of the three levels above",
  "reason": "a brief sentence explaining why it fits this level"
}}
"""

        system_instruction = (
            "You are an expert psychometrician and exam coordinator. You review academic questions "
            "and classify their difficulty tier (easy, medium, hard) accurately. You return valid JSON only."
        )

        try:
            raw_response = self.llm_provider.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.2  # Low temperature for analytical consistency
            )
            
            # Clean JSON markdown fences
            cleaned_text = raw_response.strip()
            if cleaned_text.startswith("```"):
                cleaned_text = re.sub(r"^```(?:json)?\n", "", cleaned_text)
                cleaned_text = re.sub(r"\n```$", "", cleaned_text)
            
            data = json.loads(cleaned_text.strip())
            audited_difficulty = data.get("difficulty_level", "").lower().strip()
            reason = data.get("reason", "")
        except Exception as e:
            return ValidatorResult(
                is_valid=False,
                remarks=f"Difficulty audit failed: Error parsing auditor output. Error: {str(e)}"
            )

        target_difficulty = question.difficulty_level.lower().strip()

        # Strict Checks: Extreme mismatches are rejected
        if target_difficulty == "hard" and audited_difficulty == "easy":
            return ValidatorResult(
                is_valid=False,
                remarks=(
                    f"Difficulty Mismatch: Target is 'Hard', but the AI Auditor classified it as 'Easy'. "
                    f"Reason: {reason}"
                )
            )

        if target_difficulty == "easy" and audited_difficulty == "hard":
            return ValidatorResult(
                is_valid=False,
                remarks=(
                    f"Difficulty Mismatch: Target is 'Easy', but the AI Auditor classified it as 'Hard'. "
                    f"Reason: {reason}"
                )
            )

        return ValidatorResult(is_valid=True)
