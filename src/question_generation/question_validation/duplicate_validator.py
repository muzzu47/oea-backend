from typing import Optional
from question_generation.domain.question import Question
from question_generation.application.services.embedding_service import EmbeddingService
from question_generation.repository.question_repository import QuestionRepository
from question_generation.question_validation.validator_result import ValidatorResult

class DuplicateValidator:
    """
    Tier 1 Vector-based Duplicate Validator.
    Uses pgvector similarity searches to detect conceptual/semantic duplicates.
    """

    def __init__(
        self, 
        repository: QuestionRepository, 
        embedding_service: EmbeddingService, 
        distance_threshold: float = 0.1  # Distance < 0.1 indicates high semantic duplicate
    ):
        self.repo = repository
        self.embedding_service = embedding_service
        self.threshold = distance_threshold

    def validate(self, question: Question) -> ValidatorResult:
        # Step 1: Ensure embedding exists for the new question stem
        if not question.embedding:
            try:
                question.embedding = self.embedding_service.generate_chunk_embedding(question.question)
            except Exception as e:
                return ValidatorResult(
                    is_valid=False,
                    remarks=f"Duplicate check failed: Could not generate vector embedding. Error: {str(e)}"
                )

        # Step 2: Query database for the closest semantic question
        result = self.repo.get_most_similar_question_with_distance(
            query_embedding=question.embedding,
            subject=question.subject
        )

        if result:
            closest_q, distance = result
            
            # Step 3: Flag as duplicate if distance is below threshold
            if distance < self.threshold:
                similarity_percentage = int((1.0 - distance) * 100)
                return ValidatorResult(
                    is_valid=False,
                    remarks=(
                        f"Duplicate question detected! Conceptual similarity is {similarity_percentage}% "
                        f"with existing Database ID: {closest_q.id}. (Cosine distance: {distance:.4f})"
                    )
                )

        return ValidatorResult(is_valid=True)
