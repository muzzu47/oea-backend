import os
from typing import List
from pypdf import PdfReader

class PdfParserService:
    """
    Parser service dedicated to extracting text page-by-page from PDF files.
    """

    def validate(self, file_path: str) -> bool:
        """
        Validates if the file exists and has a valid PDF magic signature.
        """
        if not os.path.exists(file_path):
            return False
        if not file_path.lower().endswith(".pdf"):
            return False
        try:
            with open(file_path, "rb") as f:
                # Check for PDF signature (%PDF-)
                header = f.read(5)
                return header.startswith(b"%PDF")
        except Exception:
            return False

    def parse(self, file_path: str) -> List[dict]:
        """
        Parses a PDF file and returns a list of pages with clean extracted text.
        Returns format: [{"page_number": int, "text": str}]
        """
        if not self.validate(file_path):
            raise ValueError(f"Invalid or missing PDF file at path: {file_path}")

        pages_data = []
        reader = PdfReader(file_path)
        
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            text = page.extract_text() or ""
            
            # Clean up white space, double spaces, and newlines
            cleaned_text = " ".join(text.split())
            if cleaned_text.strip():
                pages_data.append({
                    "page_number": page_num,
                    "text": cleaned_text
                })
        return pages_data
