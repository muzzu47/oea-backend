from typing import List
from question_generation.application.interfaces.vector_store import VectorStore
from question_generation.domain.chunk import Chunk
from question_generation.repository.textbook_repository import TextbookRepository

class PgVectorStore(VectorStore):
    """
    Concrete implementation of the VectorStore interface using PostgreSQL 
    and the pgvector extension via TextbookRepository.
    """

    def __init__(self, repository: TextbookRepository):
        self.repo = repository

    def add_chunks(self, textbook_id: int, chunks: List[Chunk]) -> None:
        """
        Stores chunks and their vector embeddings in the Postgres database using bulk inserts.
        """
        self.repo.save_chunks_bulk(textbook_id, chunks)

    def search_similar_chunks(
        self,
        query_embedding: List[float],
        subject_name: str,
        exam_type: str,
        limit: int = 5
    ) -> List[Chunk]:
        """
        Retrieves the top N most similar chunks using cosine distance vector queries.
        Translates raw database models back into pure Domain Chunk entities.
        """
        db_chunks = self.repo.get_similar_chunks(
            query_embedding=query_embedding,
            subject_name=subject_name,
            exam_type=exam_type,
            limit=limit
        )

        # Map database models back to domain Chunk entities
        domain_chunks = [
            Chunk(
                textbook_title=chunk.textbook.title,
                subject_name=chunk.subject_name,
                chapter_name="unassigned",  # Mapped dynamically during generation
                content=chunk.content,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                concept_name=chunk.concept_name,
                exam_type=chunk.exam_type,
                embedding=chunk.embedding
            )
            for chunk in db_chunks
        ]
        return domain_chunks
