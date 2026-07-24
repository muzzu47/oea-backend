import logging
from typing import List, Optional

from question_generation.domain.textbook import Textbook
from question_generation.domain.textbook_parsed_page import TextbookParsedPage
from question_generation.domain.chunk import Chunk
from question_generation.ingestion_parser.pdf_parser_service import PdfParserService
from question_generation.application.services.embedding_service import EmbeddingService
from question_generation.repository.textbook_repository import TextbookRepository

logger = logging.getLogger(__name__)

class IngestTextbookOrchestrator:
    """
    Orchestrator responsible for executing the complete use-case workflow of
    textbook ingestion:
    1. Parsing PDF pages into raw text using PdfParserService.
    2. Storing raw parsed pages into the database.
    3. Segmenting raw pages into overlapping chunks.
    4. Generating vector embeddings in bulk using EmbeddingService.
    5. Storing chunks and their vectors into pgvector database via TextbookRepository.
    """

    def __init__(
        self,
        parser: PdfParserService,
        embedding_service: EmbeddingService,
        textbook_repository: TextbookRepository,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.parser = parser
        self.embedding_service = embedding_service
        self.repo = textbook_repository
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def execute(
        self,
        file_path: str,
        title: str,
        subject_name: str,
        author: Optional[str] = None,
        exam_type: Optional[str] = None
    ) -> dict:
        """
        Runs the textbook ingestion use case workflow.
        Returns a dictionary representing the operation results or failure metrics.
        """
        # Step 1: Parse the PDF (with automatic Gemini OCR fallback if local parser returns 0 text)
        try:
            llm_provider = getattr(self.embedding_service, "llm_provider", None)
            pages_data = self.parser.parse(file_path, llm_provider=llm_provider)
            logger.info(f"Step 1: Parsed {len(pages_data)} pages from PDF file.")
        except Exception as e:
            logger.error(f"Step 1 Failed: PDF parsing failed: {str(e)}")
            return {"status": "failed", "stage": "parsing", "error": str(e)}

        # Step 2: Register textbook metadata and store raw pages
        try:
            db_textbook = self.repo.get_textbook_by_title(title)
            if not db_textbook:
                domain_textbook = Textbook(
                    title=title,
                    subject_name=subject_name,
                    file_path=file_path,
                    author=author,
                    exam_type=exam_type
                )
                db_textbook = self.repo.save_textbook(domain_textbook)
            
            textbook_id = db_textbook.id

            # Save raw parsed pages to database
            domain_pages = [
                TextbookParsedPage(
                    textbook_title=title,
                    page_number=page["page_number"],
                    content=page["text"],
                    subject_name=subject_name,
                    exam_type=exam_type
                )
                for page in pages_data
            ]
            self.repo.save_parsed_pages_bulk(textbook_id, domain_pages)
            logger.info(f"Step 2: Saved {len(domain_pages)} parsed pages to Postgres.")
        except Exception as e:
            logger.error(f"Step 2 Failed: Saving parsed pages to database failed: {str(e)}")
            return {"status": "failed", "stage": "saving_pages", "error": str(e)}

        # Step 3: Segment pages into overlapping text chunks
        try:
            chunks = self.chunk_text(pages_data, title, subject_name, exam_type)
            logger.info(f"Step 3: Created {len(chunks)} overlapping text chunks.")
        except Exception as e:
            logger.error(f"Step 3 Failed: Chunking text failed: {str(e)}")
            return {"status": "failed", "stage": "chunking", "error": str(e)}

        # Step 4: Bulk generate vector embeddings
        try:
            chunk_contents = [c.content for c in chunks]
            # Call our decoupled EmbeddingService to get batch embeddings
            embeddings = self.embedding_service.generate_chunk_embeddings_bulk(chunk_contents)
            
            for idx, emb in enumerate(embeddings):
                chunks[idx].embedding = emb
            logger.info("Step 4: Vector embeddings computed successfully via LLM Provider.")
        except Exception as e:
            logger.error(f"Step 4 Failed: Embedding calculation failed: {str(e)}")
            return {"status": "failed", "stage": "embedding", "error": str(e)}

        # Step 5: Save chunks and vector embeddings to database
        try:
            self.repo.save_chunks_bulk(textbook_id, chunks)
            logger.info(f"Step 5: Saved {len(chunks)} chunks and vectors to pgvector.")
        except Exception as e:
            logger.error(f"Step 5 Failed: Saving chunks to pgvector failed: {str(e)}")
            return {"status": "failed", "stage": "saving_chunks", "error": str(e)}

        return {
            "status": "success",
            "textbook_id": textbook_id,
            "pages_parsed": len(pages_data),
            "chunks_created": len(chunks)
        }

    def chunk_text(
        self,
        pages_data: List[dict],
        textbook_title: str,
        subject_name: str,
        exam_type: Optional[str] = None
    ) -> List[Chunk]:
        """
        Helper method to split raw page texts into standard overlapping chunks.
        """
        chunks: List[Chunk] = []
        chunk_idx = 0

        for page in pages_data:
            page_num = page["page_number"]
            text = page["text"]

            start = 0
            text_len = len(text)

            while start < text_len:
                end = min(start + self.chunk_size, text_len)
                chunk_text = text[start:end]

                chunk = Chunk(
                    textbook_title=textbook_title,
                    subject_name=subject_name,
                    chapter_name="unassigned",  # Will be mapped to chapters later
                    content=chunk_text,
                    page_number=page_num,
                    chunk_index=chunk_idx,
                    exam_type=exam_type
                )
                chunks.append(chunk)
                chunk_idx += 1

                start += (self.chunk_size - self.chunk_overlap)

                if end == text_len:
                    break

        return chunks
