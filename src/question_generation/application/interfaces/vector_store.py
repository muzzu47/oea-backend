from abc import ABC, abstractmethod
from typing import List, Optional
from question_generation.domain.chunk import Chunk

class VectorStore(ABC):
    """
    Abstract interface for Vector Store operations.
    Decouples core business services from specific vector database vendors (e.g. pgvector, Pinecone).
    """

    @abstractmethod
    def add_chunks(self, textbook_id: int, chunks: List[Chunk]) -> None:
        """
        Stores chunks and their vector embeddings in the vector database.
        """
        pass

    @abstractmethod
    def search_similar_chunks(
        self,
        query_embedding: List[float],
        subject_name: str,
        exam_type: str,
        limit: int = 5
    ) -> List[Chunk]:
        """
        Retrieves the top N most similar chunks based on vector distance,
        filtered by subject and exam type.
        """
        pass
