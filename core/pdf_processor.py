from pypdf import PdfReader
import re
from typing import List, Dict, Any

def clean_text(text: str) -> str:
    """Cleans null bytes and extra whitespace from text."""
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def process_pdf(pdf_path: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Reads a PDF and returns a list of text chunks with page numbers.
    """
    reader = PdfReader(pdf_path)
    documents: List[Dict[str, Any]] = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue

        text = clean_text(text)

        # Create overlapping chunks
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]

            # Filter out very small fragments
            if len(chunk.strip()) < 50:
                continue

            documents.append({
                "text": chunk,
                "page": page_num
            })

    return documents