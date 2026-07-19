from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class TextbookParsedPage:
    """
    Represents the raw, un-chunked text extracted from a single PDF page.
    Stored in the database as the permanent source of truth for the book's content.
    """
    textbook_title: str
    page_number: int
    content: str
    subject_name: str
    exam_type: Optional[str] = None
