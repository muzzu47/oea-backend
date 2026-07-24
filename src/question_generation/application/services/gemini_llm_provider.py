import os
from typing import List, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

from question_generation.application.interfaces.llm_provider import LlmProvider

class GeminiLlmProvider(LlmProvider):
    """
    Concrete implementation of the LlmProvider interface using the Google GenAI SDK.
    Handles both question text generation and vector embedding creation.
    """

    def __init__(
        self, 
        generation_model: str = "gemini-2.5-flash",
        embedding_model: str = "text-embedding-004"
    ):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API Key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY in your environment/dotenv."
            )
        self.client = genai.Client(api_key=api_key)
        self.generation_model = generation_model
        self.embedding_model = embedding_model

    def generate_text(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generates a text response (e.g. MCQs) using the configured Gemini Flash model.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        try:
            response = self.client.models.generate_content(
                model=self.generation_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature
                )
            )
            return response.text or ""
        except APIError as e:
            raise RuntimeError(f"Gemini Text Generation API Error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during text generation: {str(e)}")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a 768-dimensional vector embedding for a single text chunk.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty for embedding.")

        try:
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text
            )
            return response.embeddings[0].values
        except APIError as e:
            raise RuntimeError(f"Gemini Embedding API Error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during embedding generation: {str(e)}")

    def generate_embeddings_bulk(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Generates vector embeddings for a list of strings in batches.
        """
        if not texts:
            return []

        embeddings: List[List[float]] = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self.client.models.embed_content(
                    model=self.embedding_model,
                    contents=batch
                )
                embeddings.extend([e.values for e in response.embeddings])
            except APIError as e:
                raise RuntimeError(f"Gemini Bulk Embedding API Error on batch starting at index {i}: {str(e)}")
            except Exception as e:
                raise RuntimeError(f"Unexpected error in bulk embedding: {str(e)}")
                
        return embeddings

    def extract_pdf_content(self, file_path: str) -> List[dict]:
        """
        Uses Gemini 2.5 Flash Multimodal API to parse scanned or image-heavy PDFs page-by-page.
        Returns format: [{"page_number": int, "text": str}]
        """
        import json
        import logging
        logger = logging.getLogger(__name__)
        
        if not os.path.exists(file_path):
            raise ValueError(f"File not found for Gemini OCR: {file_path}")

        logger.info(f"Uploading '{file_path}' to Gemini File API for Multimodal OCR parsing...")
        uploaded_file = self.client.files.upload(file=file_path)
        
        try:
            prompt = (
                "Extract all text content from this textbook PDF document page by page. "
                "Preserve all body text, section headers, key terms, definitions, and mathematical expressions. "
                "Format your entire response strictly as a JSON array of objects with the keys 'page_number' (integer) and 'text' (string). "
                "Example format: [{\"page_number\": 1, \"text\": \"Chapter 1: Units and Measurement...\"}]"
            )

            response = self.client.models.generate_content(
                model=self.generation_model,
                contents=[uploaded_file, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

            raw_text = response.text or "[]"
            pages_data = json.loads(raw_text)
            
            formatted_pages = []
            if isinstance(pages_data, list):
                for p in pages_data:
                    if isinstance(p, dict) and "text" in p and p["text"].strip():
                        formatted_pages.append({
                            "page_number": int(p.get("page_number", len(formatted_pages) + 1)),
                            "text": str(p["text"]).strip()
                        })
            
            logger.info(f"Gemini OCR successfully extracted text from {len(formatted_pages)} pages.")
            return formatted_pages
            
        except APIError as e:
            raise RuntimeError(f"Gemini OCR API Error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during Gemini OCR parsing: {str(e)}")
        finally:
            # Clean up uploaded file from Gemini storage
            try:
                self.client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
