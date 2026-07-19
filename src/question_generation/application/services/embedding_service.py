import os
from typing import List
from google import genai
from google.genai.errors import APIError

class EmbeddingService:
    """
    Service responsible for communicating with Google Gemini API to generate
    high-dimensional vector embeddings for text chunks.
    """

    def __init__(self, model_name: str = "text-embedding-004"):
        # Initialize Google Gen AI client.
        # Checks GEMINI_API_KEY or GOOGLE_API_KEY from environment variables.
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API Key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY in your environment/dotenv."
            )
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding for a single text string.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")
            
        try:
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=text
            )
            return response.embeddings[0].values
        except APIError as e:
            raise RuntimeError(f"Gemini Embedding API Error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during embedding generation: {str(e)}")

    def get_embeddings_bulk(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Generates vector embeddings for a list of strings in batches.
        Prevents hitting API payload limits and optimizes token throughput.
        """
        if not texts:
            return []

        embeddings: List[List[float]] = []
        
        # Batch texts to prevent overloading the request size
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=batch
                )
                embeddings.extend([e.values for e in response.embeddings])
            except APIError as e:
                raise RuntimeError(f"Gemini Bulk Embedding API Error on batch starting at index {i}: {str(e)}")
            except Exception as e:
                raise RuntimeError(f"Unexpected error in bulk embedding: {str(e)}")
                
        return embeddings
