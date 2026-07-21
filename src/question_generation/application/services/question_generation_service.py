import json
import re
from typing import List, Optional

from question_generation.application.interfaces.llm_provider import LlmProvider
from question_generation.domain.chunk import Chunk
from question_generation.domain.question import Question

class QuestionGenerationService:
    """
    Business service responsible for constructing generation prompts,
    calling the LLM provider, and parsing raw outputs into domain Question objects.
    """

    def __init__(self, llm_provider: LlmProvider):
        self.llm_provider = llm_provider

    def generate_questions_from_context(
        self,
        context_chunks: List[Chunk],
        count: int,
        difficulty_level: str,
        subject: str,
        chapter: str,
        exam_type: Optional[str] = None
    ) -> List[Question]:
        """
        Assembles textbook context, sends a structured prompt to the LLM,
        and parses the response into domain Question objects.
        """
        if not context_chunks:
            raise ValueError("No context chunks provided for question generation.")

        # Step 1: Combine context chunk contents
        context_text = "\n\n".join(
            [f"[Source Page {c.page_number}]: {c.content}" for c in context_chunks]
        )

        # Step 2: Formulate prompt templates
        prompt = f"""
Based on the following textbook context, generate exactly {count} multiple-choice question(s).

Textbook Context:
{context_text}

Requirements for the generated questions:
1. Difficulty Level: {difficulty_level}
2. Subject: {subject}
3. Chapter: {chapter}
4. Each question must have exactly 4 options.
5. Identify the correct option and provide a step-by-step solution/explanation.

You MUST respond ONLY with a JSON object matching this structure:
{{
  "questions": [
    {{
      "topic": "Specific sub-topic name",
      "concept": "Specific cognitive concept tested",
      "topic_weightage": "normal",
      "question": "Question stem text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "solution": "Step-by-step explanation why the correct answer is correct"
    }}
  ]
}}
"""

        system_instruction = (
            "You are an expert academic curriculum author. You generate highly accurate "
            "multiple-choice questions from source textbook text. You output strict, valid JSON only."
        )

        # Step 3: Call LLM Provider
        raw_response = self.llm_provider.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.7
        )

        # Step 4: Parse raw text output to domain entities
        return self._parse_json_response(raw_response, subject, chapter, exam_type, context_chunks)

    def _parse_json_response(
        self, 
        raw_text: str, 
        subject: str, 
        chapter: str,
        exam_type: Optional[str],
        context_chunks: List[Chunk]
    ) -> List[Question]:
        """
        Cleans LLM formatting artifacts and parses the response into domain models.
        """
        # Strip markdown code fences if present (e.g. ```json ... ```)
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```"):
            # Remove leading ```json or ```
            cleaned_text = re.sub(r"^```(?:json)?\n", "", cleaned_text)
            # Remove trailing ```
            cleaned_text = re.sub(r"\n```$", "", cleaned_text)
        cleaned_text = cleaned_text.strip()

        try:
            data = json.loads(cleaned_text)
            questions_data = data.get("questions", [])
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Failed to parse LLM response as JSON. Error: {str(e)}. Raw text was: {raw_text}"
            )

        domain_questions: List[Question] = []
        
        # Determine source chunk mapping (link to the first chunk in context for traceability)
        default_chunk_id = None
        if context_chunks:
            # We will map chunk ID at the orchestration layer, or keep track of metadata.
            # For now, default_chunk_id remains None and is injected by database save.
            pass

        for item in questions_data:
            # Validate option list length
            options = item.get("options", [])
            if len(options) != 4:
                # Skip invalid question layouts or handle gracefully
                continue

            question = Question(
                subject=subject,
                chapter=chapter,
                topic=item.get("topic", "General"),
                concept=item.get("concept", "General"),
                topic_weightage=item.get("topic_weightage", "normal"),
                question=item.get("question", ""),
                options=options,
                correct_answer=item.get("correct_answer", ""),
                solution=item.get("solution", ""),
                difficulty_level=item.get("difficulty_level", "medium"),
                question_type="single_correct",
                exam_type=exam_type,
                generated_by="ai",
                validation_status="generated"
            )
            domain_questions.append(question)

        return domain_questions
