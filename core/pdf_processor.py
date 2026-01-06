from pypdf import PdfReader
import re
from typing import List, Dict, Any

def clean_text(text: str) -> str:
    """Cleans null bytes and extra whitespace from text."""
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def process_pdf(pdf_path: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """
    Reads a PDF and returns a list of text chunks with page numbers.
    Uses sentence-aware chunking to avoid breaking mid-sentence.
    
    Args:
        pdf_path: Path to the PDF file
        chunk_size: Target size for each chunk (characters)
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of dictionaries containing text chunks and page numbers
    """
    try:
        reader = PdfReader(pdf_path)
    except Exception as e:
        raise Exception(f"Failed to read PDF: {str(e)}")
    
    documents: List[Dict[str, Any]] = []

    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text()
        except Exception as e:
            print(f"Warning: Could not extract text from page {page_num}: {e}")
            continue
            
        if not text or len(text.strip()) < 10:
            continue

        text = clean_text(text)
        
        # Split into sentences to avoid breaking mid-sentence
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            # If adding this sentence exceeds chunk_size, save current chunk
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                if len(current_chunk.strip()) >= 100:
                    documents.append({
                        "text": current_chunk.strip(),
                        "page": page_num
                    })
                # Start new chunk with overlap
                words = current_chunk.split()
                overlap_words = words[-int(overlap/5):] if len(words) > overlap/5 else words
                current_chunk = " ".join(overlap_words) + " " + sentence + " "
            else:
                current_chunk += sentence + " "
        
        # Add remaining text from this page
        if len(current_chunk.strip()) >= 100:
            documents.append({
                "text": current_chunk.strip(),
                "page": page_num
            })

    if not documents:
        raise Exception("No text content could be extracted from the PDF")
    
    return documents