import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class PdfParserService:
    """
    Parser service dedicated to extracting text page-by-page from PDF files.
    Employs 100% free, local Python PDF engines with $0 API cost:
    1. pdfplumber (best for layout preservation, tables, and complex typesetting)
    2. PyMuPDF / fitz (ultra-fast C engine for custom font streams)
    3. pypdf (lightweight fallback)
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
                header = f.read(5)
                return header.startswith(b"%PDF")
        except Exception:
            return False

    def parse(self, file_path: str, llm_provider: Optional[object] = None) -> List[dict]:
        """
        Parses a PDF file using local Python engines.
        Returns format: [{"page_number": int, "text": str}]
        """
        if not self.validate(file_path):
            raise ValueError(f"Invalid or missing PDF file at path: {file_path}")

        file_size = os.path.getsize(file_path)
        logger.info(f"Local PDF Parser opened '{file_path}' ({file_size} bytes).")

        # --- Engine 1: pdfplumber (Highest Precision for layout/math) ---
        pages_data = self._parse_with_pdfplumber(file_path)
        if pages_data:
            logger.info(f"Engine 1 (pdfplumber) succeeded: extracted text from {len(pages_data)} pages.")
            return pages_data

        # --- Engine 2: PyMuPDF / fitz (C-Engine Fallback) ---
        pages_data = self._parse_with_pymupdf(file_path)
        if pages_data:
            logger.info(f"Engine 2 (PyMuPDF / fitz) succeeded: extracted text from {len(pages_data)} pages.")
            return pages_data

        # --- Engine 3: pypdf (Standard Fallback) ---
        pages_data = self._parse_with_pypdf(file_path)
        if pages_data:
            logger.info(f"Engine 3 (pypdf) succeeded: extracted text from {len(pages_data)} pages.")
            return pages_data

        logger.error(
            f"All local PDF engines extracted 0 text from '{file_path}' ({file_size} bytes). "
            "The document is likely an image-only scanned document."
        )
        return []

    def _parse_with_pdfplumber(self, file_path: str) -> List[dict]:
        try:
            import pdfplumber
            pages_data = []
            with pdfplumber.open(file_path) as pdf:
                for idx, page in enumerate(pdf.pages):
                    text = page.extract_text(layout=True) or page.extract_text() or ""
                    cleaned_text = " ".join(text.split())
                    if cleaned_text.strip():
                        pages_data.append({
                            "page_number": idx + 1,
                            "text": cleaned_text
                        })
            return pages_data
        except ImportError:
            logger.debug("pdfplumber is not installed.")
            return []
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return []

    def _parse_with_pymupdf(self, file_path: str) -> List[dict]:
        try:
            import fitz  # PyMuPDF
            pages_data = []
            doc = fitz.open(file_path)
            for idx, page in enumerate(doc):
                text = page.get_text("text") or page.get_text("blocks") or ""
                if isinstance(text, list):
                    text = " ".join([b[4] for b in text if len(b) >= 5 and isinstance(b[4], str)])
                cleaned_text = " ".join(str(text).split())
                if cleaned_text.strip():
                    pages_data.append({
                        "page_number": idx + 1,
                        "text": cleaned_text
                    })
            doc.close()
            return pages_data
        except ImportError:
            logger.debug("PyMuPDF (fitz) is not installed.")
            return []
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")
            return []

    def _parse_with_pypdf(self, file_path: str) -> List[dict]:
        try:
            from pypdf import PdfReader
            pages_data = []
            reader = PdfReader(file_path)
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                cleaned_text = " ".join(text.split())
                if cleaned_text.strip():
                    pages_data.append({
                        "page_number": idx + 1,
                        "text": cleaned_text
                    })
            return pages_data
        except Exception as e:
            logger.warning(f"pypdf extraction failed: {e}")
            return []
