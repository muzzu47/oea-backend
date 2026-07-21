from typing import List
from question_generation.application.interfaces.llm_provider import LlmProvider

class EmbeddingService:
    """
    Business service responsible for coordinating vector embedding generation
    for textbook chunks using an abstract LLM Provider.
    """

    def __init__(self, llm_provider: LlmProvider):
        # Inject the abstract LlmProvider interface, not the concrete Gemini client
        self.llm_provider = llm_provider

    def generate_chunk_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding for a single text chunk.
        """
        return self.llm_provider.generate_embedding(text)

    def generate_chunk_embeddings_bulk(self, texts: List[str]) -> List[List[float]]:
        """
        Generates vector embeddings for a list of chunks in bulk.
        """
        return self.llm_provider.generate_embeddings_bulk(texts)
