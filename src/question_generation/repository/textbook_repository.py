from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from question_generation.domain.textbook import Textbook
from question_generation.domain.textbook_parsed_page import TextbookParsedPage
from question_generation.domain.chunk import Chunk
from question_generation.repository.database_models import (
    TextbookModel, 
    TextbookParsedPageModel, 
    TextbookChunkModel
)

class TextbookRepository:
    """
    Repository responsible for handling all database operations for Textbooks,
    extracted raw pages, and vector search operations on chunks.
    """

    def __init__(self, db: Session):
        self.db = db

    def save_textbook(self, textbook: Textbook) -> TextbookModel:
        """
        Saves a new textbook metadata record to the database.
        """
        db_textbook = TextbookModel(
            title=textbook.title,
            subject_name=textbook.subject_name,
            file_path=textbook.file_path,
            author=textbook.author,
            exam_type=textbook.exam_type
        )
        self.db.add(db_textbook)
        self.db.commit()
        self.db.refresh(db_textbook)
        return db_textbook

    def get_textbook_by_title(self, title: str) -> Optional[TextbookModel]:
        """
        Retrieves textbook metadata by title.
        """
        stmt = select(TextbookModel).where(TextbookModel.title == title)
        return self.db.scalars(stmt).first()

    def save_parsed_pages_bulk(self, textbook_id: int, pages: List[TextbookParsedPage]):
        """
        Saves a batch of raw extracted pages to the database using SQLAlchemy 2.0 bulk syntax.
        """
        if not pages:
            return

        db_pages = [
            {
                "textbook_id": textbook_id,
                "page_number": page.page_number,
                "content": page.content,
                "subject_name": page.subject_name,
                "exam_type": page.exam_type
            }
            for page in pages
        ]
        
        # Optimized bulk insert mapping
        self.db.run_validators = False  # Disable validation overhead for speed
        self.db.bulk_insert_mappings(TextbookParsedPageModel, db_pages)
        self.db.commit()

    def save_chunks_bulk(self, textbook_id: int, chunks: List[Chunk]):
        """
        Saves a batch of chunks along with vector embeddings using bulk syntax.
        """
        if not chunks:
            return

        db_chunks = [
            {
                "textbook_id": textbook_id,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "concept_name": chunk.concept_name,
                "subject_name": chunk.subject_name,
                "exam_type": chunk.exam_type,
                "embedding": chunk.embedding
            }
            for chunk in chunks
        ]

        # Optimized bulk insert mapping
        self.db.bulk_insert_mappings(TextbookChunkModel, db_chunks)
        self.db.commit()

    def get_similar_chunks(
        self,
        query_embedding: List[float],
        subject_name: str,
        exam_type: str,
        limit: int = 5
    ) -> List[TextbookChunkModel]:
        """
        Performs a vector similarity search (cosine distance) to find the most 
        relevant textbook chunks, filtered by subject and exam type.
        """
        # Cosine distance: 0 is identical, 2 is opposite.
        # Order by closest distance first.
        stmt = (
            select(TextbookChunkModel)
            .where(
                TextbookChunkModel.subject_name == subject_name,
                TextbookChunkModel.exam_type == exam_type
            )
            .order_by(TextbookChunkModel.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
