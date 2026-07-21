import logging
from typing import List, Optional

from question_generation.application.interfaces.vector_store import VectorStore
from question_generation.application.services.embedding_service import EmbeddingService
from question_generation.application.services.question_generation_service import QuestionGenerationService
from question_generation.application.services.question_validation_service import QuestionValidationService
from question_generation.repository.question_repository import QuestionRepository

logger = logging.getLogger(__name__)

class GenerateQuestionsOrchestrator:
    """
    Orchestrator responsible for executing the question generation and validation use case.
    Coordinates RAG search, batch generation, multi-tier validation, and database storage.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        generation_service: QuestionGenerationService,
        validation_service: QuestionValidationService,
        question_repository: QuestionRepository
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.gen_service = generation_service
        self.val_service = validation_service
        self.repo = question_repository

    def execute(
        self,
        subject: str,
        chapter: str,
        concept: str,
        difficulty: str,
        target_count: int,
        exam_type: Optional[str] = None
    ) -> dict:
        """
        Executes the question generation loop.
        Generates, validates, and stores questions in batches until target_count is reached
        or max_attempts circuit breaker is tripped.
        """
        logger.info(
            f"Starting generation orchestrator: Subject={subject}, Chapter={chapter}, "
            f"Concept={concept}, Target={target_count}, Difficulty={difficulty}"
        )

        # Step 1: Create search embedding for the concept
        try:
            query_text = f"Concept: {concept}. Chapter: {chapter}. Subject: {subject}."
            query_vector = self.embedding_service.generate_chunk_embedding(query_text)
        except Exception as e:
            logger.error(f"Failed to generate query vector: {str(e)}")
            return {"status": "failed", "stage": "query_embedding", "error": str(e)}

        # Step 2: Retrieve matching text chunks from the vector store
        try:
            chunks = self.vector_store.search_similar_chunks(
                query_embedding=query_vector,
                subject_name=subject,
                exam_type=exam_type,
                limit=10  # Retrieve top 10 relevant context passages
            )
            if not chunks:
                logger.warning("No context chunks retrieved for this concept. Question generation aborted.")
                return {
                    "status": "failed",
                    "stage": "retrieval",
                    "error": f"No textbook context found matching concept '{concept}'."
                }
            logger.info(f"Retrieved {len(chunks)} relevant textbook context chunks.")
        except Exception as e:
            logger.error(f"Failed to retrieve chunks: {str(e)}")
            return {"status": "failed", "stage": "retrieval", "error": str(e)}

        # Step 3: Batch generation and validation loop
        saved_question_ids: List[int] = []
        failed_attempts = 0
        max_attempts = target_count * 3  # Circuit breaker threshold
        chunk_index = 0

        while len(saved_question_ids) < target_count and failed_attempts < max_attempts:
            # Determine count needed for this batch (max 3 at a time)
            remaining_needed = target_count - len(saved_question_ids)
            batch_size = min(3, remaining_needed)

            # Slide through retrieved context chunks for varying prompts
            context_slice = chunks[chunk_index : chunk_index + 2]
            # Wrap around chunk index if we exceed chunk size
            chunk_index = (chunk_index + 1) % (len(chunks) - 1 if len(chunks) > 1 else 1)

            logger.info(
                f"Generating batch of {batch_size}. Saved: {len(saved_question_ids)}/{target_count}. "
                f"Failed attempts: {failed_attempts}/{max_attempts}."
            )

            try:
                # Generate raw batch
                generated_questions = self.gen_service.generate_questions_from_context(
                    context_chunks=context_slice,
                    count=batch_size,
                    difficulty_level=difficulty,
                    subject=subject,
                    chapter=chapter,
                    exam_type=exam_type
                )
            except Exception as e:
                logger.warning(f"Batch generation failed: {str(e)}")
                failed_attempts += batch_size
                continue

            # Validate each question in the generated batch
            for q in generated_questions:
                # Add current concept & difficulty details to domain before validation
                q.concept = concept
                q.difficulty_level = difficulty

                # Run validation pipeline (Tier 1 & Tier 2 checks)
                val_result = self.val_service.validate_question(q)

                if val_result.is_valid:
                    try:
                        # Save valid question to repository
                        db_q = self.repo.save(q)
                        saved_question_ids.append(db_q.id)
                        logger.info(f"Successfully validated and saved Question ID: {db_q.id}")
                    except Exception as e:
                        logger.error(f"Failed to save validated question: {str(e)}")
                        failed_attempts += 1
                else:
                    logger.warning(f"Question validation failed: {val_result.remarks}")
                    failed_attempts += 1

        # Step 4: Summarize results
        status = "success" if len(saved_question_ids) == target_count else "partial_success"
        if failed_attempts >= max_attempts:
            logger.error("Generation stopped: Circuit breaker tripped due to excessive validation failures.")
            status = "tripped"

        return {
            "status": status,
            "subject": subject,
            "chapter": chapter,
            "concept": concept,
            "target_count": target_count,
            "generated_count": len(saved_question_ids),
            "saved_ids": saved_question_ids,
            "failed_attempts": failed_attempts
        }
