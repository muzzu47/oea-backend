import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from question_generation.domain.textbook import Textbook
from question_generation.domain.textbook_parsed_page import TextbookParsedPage
from question_generation.domain.chunk import Chunk
from question_generation.ingestion_parser.pdf_parser_service import PdfParserService
from question_generation.application.services.embedding_service import EmbeddingService
from question_generation.repository.textbook_repository import TextbookRepository

logger = logging.getLogger(__name__)

class IngestionService:
    """
    Service responsible for orchestrating the complete ingestion pipeline:
    1. Parse PDF pages to raw text (delegated to PdfParserService).
    2. Save raw pages to PostgreSQL.
    3. Segment raw pages into overlapping semantic chunks.
    4. Call EmbeddingService to generate vector embeddings.
    5. Save chunks and embeddings into PostgreSQL (pgvector).
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

    def ingest_new_textbook(
        self,
        file_path: str,
        title: str,
        subject_name: str,
        author: Optional[str] = None,
        exam_type: Optional[str] = None
    ) -> dict:
        """
        Runs the complete, multi-stage ingestion pipeline with error handling.
        Returns a dictionary summarizing results or errors.
        """
        logger.info(f"Starting ingestion for textbook: {title}")
        
        # Step 1: Parse the PDF to raw pages
        try:
            pages_data = self.parser.parse(file_path)
            logger.info(f"Successfully extracted {len(pages_data)} pages from PDF.")
        except Exception as e:
            logger.error(f"Failed to parse PDF file: {str(e)}")
            return {"status": "failed", "stage": "parsing", "error": str(e)}

        # Step 2: Register textbook and save raw pages to database
        try:
            # Check if textbook already exists
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
            
            # Map raw page dictionaries to domain models
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
            logger.info(f"Saved {len(domain_pages)} parsed pages to database.")
        except Exception as e:
            logger.error(f"Failed to save parsed pages to database: {str(e)}")
            return {"status": "failed", "stage": "saving_pages", "error": str(e)}

        # Step 3: Segment pages into chunks
        try:
            chunks = self.chunk_text(pages_data, title, subject_name, exam_type)
            logger.info(f"Generated {len(chunks)} text chunks.")
        except Exception as e:
            logger.error(f"Failed to segment text into chunks: {str(e)}")
            return {"status": "failed", "stage": "chunking", "error": str(e)}

        # Step 4: Compute Embeddings (External API Calls)
        try:
            chunk_contents = [c.content for c in chunks]
            # Bulk generate embeddings in batches
            embeddings = self.embedding_service.get_embeddings_bulk(chunk_contents)
            
            # Assign vector embeddings back to chunks
            for idx, emb in enumerate(embeddings):
                chunks[idx].embedding = emb
            logger.info("Successfully generated embeddings for all chunks.")
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            return {"status": "failed", "stage": "embedding", "error": str(e)}

        # Step 5: Save chunks and vectors in bulk
        try:
            self.repo.save_chunks_bulk(textbook_id, chunks)
            logger.info(f"Successfully saved {len(chunks)} chunks and vectors to database.")
        except Exception as e:
            logger.error(f"Failed to save chunks and vectors to database: {str(e)}")
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
        Splits pages_data text into standard overlapping chunks.
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
                
                # Advance window subtracting overlap
                start += (self.chunk_size - self.chunk_overlap)
                
                if end == text_len:
                    break
                    
        return chunks
