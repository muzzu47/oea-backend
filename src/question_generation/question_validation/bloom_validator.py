import json
import re
from typing import Optional

from question_generation.application.interfaces.llm_provider import LlmProvider
from question_generation.domain.question import Question
from question_generation.question_validation.validator_result import ValidatorResult

class BloomValidator:
    """
    Tier 2 AI Auditor.
    Prompts the LLM to audit the question's Bloom's Taxonomy level,
    ensuring cognitive depth matches the difficulty tier.
    """

    def __init__(self, llm_provider: LlmProvider):
        self.llm_provider = llm_provider

    def validate(self, question: Question) -> ValidatorResult:
        # Prompt Gemini to audit the cognitive level
        prompt = f"""
Analyze the following multiple-choice question and classify its cognitive level under Bloom's Taxonomy.

Question:
{question.question}

Options:
{question.options}

Correct Answer:
{question.correct_answer}

Explanation:
{question.solution}

Select exactly one of these Bloom's levels:
- remember
- understand
- apply
- analyze
- evaluate
- create

You MUST respond ONLY with a JSON object in this format:
{{
  "blooms_level": "one of the six levels above",
  "reason": "a brief sentence explaining why it belongs to this level"
}}
"""

        system_instruction = (
            "You are an expert academic auditor and psychometrician. You evaluate test questions "
            "and classify them accurately using Bloom's Taxonomy cognitive categories. You return valid JSON only."
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
            blooms_level = data.get("blooms_level", "").lower().strip()
            reason = data.get("reason", "")
        except Exception as e:
            return ValidatorResult(
                is_valid=False,
                remarks=f"Bloom's audit failed: Error parsing auditor output. Error: {str(e)}"
            )

        # Audit Rigour Check: Compare Blooms level with Question Difficulty
        difficulty = question.difficulty_level.lower().strip()

        # Rule 1: A "hard" question must not be a basic recall/understanding question
        if difficulty == "hard" and blooms_level in ["remember", "understand"]:
            return ValidatorResult(
                is_valid=False,
                remarks=(
                    f"Bloom's Taxonomy Mismatch: Question difficulty is set to 'Hard', but the AI Auditor "
                    f"classified it as '{blooms_level}' (Rote Recall/Basic Understanding). "
                    f"Reason: {reason}"
                )
            )

        # Rule 2: An "easy" question should not require complex evaluation/creation
        if difficulty == "easy" and blooms_level in ["evaluate", "create"]:
            return ValidatorResult(
                is_valid=False,
                remarks=(
                    f"Bloom's Taxonomy Mismatch: Question difficulty is set to 'Easy', but the AI Auditor "
                    f"classified it as '{blooms_level}' (Complex evaluation/creation). "
                    f"Reason: {reason}"
                )
            )

        return ValidatorResult(is_valid=True)
