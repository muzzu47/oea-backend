from abc import ABC, abstractmethod
from typing import List, Optional

class LlmProvider(ABC):
    """
    Abstract interface for Large Language Model (LLM) providers.
    Enables swapping Google Gemini API for OpenAI, Anthropic, or local open-source models (like LLaMA).
    """

    @abstractmethod
    def generate_text(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generates a text response from the LLM based on the given prompt.
        """
        pass

    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding (list of floats) for a single string.
        """
        pass

    @abstractmethod
    def generate_embeddings_bulk(self, texts: List[str]) -> List[List[float]]:
        """
        Generates vector embeddings for a list of strings in batches.
        """
        pass
