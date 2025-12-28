import os
from typing import List, Dict

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# -----------------------------
# PDF Processing
# -----------------------------
def process_pdf(
    pdf_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Dict]:
    """
    Extracts text from a PDF, splits it into chunks, and returns documents
    compatible with the embedding pipeline.

    Returns:
        List of dicts with keys: 'text', 'page'
    """

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF: {e}")

    documents: List[Dict] = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text()
        except Exception:
            # Some PDF pages may be corrupted
            continue

        if not text or not text.strip():
            continue

        # Normalize text
        text = text.replace("\x00", " ").strip()

        chunks = splitter.split_text(text)

        for chunk in chunks:
            if not chunk.strip():
                continue

            documents.append({
                "text": chunk.strip(),
                "page": page_number
            })

    if not documents:
        raise ValueError("No extractable text found in the PDF.")

    return documents
