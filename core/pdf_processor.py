from pypdf import PdfReader
import fitz  # PyMuPDF
import base64
import re
from typing import List, Dict, Any
from io import BytesIO
from PIL import Image

def clean_text(text: str) -> str:
    """Cleans null bytes and extra whitespace from text."""
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_images_from_pdf(pdf_path: str, max_images_per_page: int = 3) -> Dict[int, List[str]]:
    """
    Extracts images from PDF and returns them as base64 strings organized by page.
    
    Args:
        pdf_path: Path to the PDF file
        max_images_per_page: Maximum number of images to extract per page
    
    Returns:
        Dictionary mapping page numbers to lists of base64-encoded images
    """
    try:
        doc = fitz.open(pdf_path)
        page_images = {}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            page_images[page_num + 1] = []
            
            # Limit images per page to avoid overwhelming the API
            for img_index, img in enumerate(image_list[:max_images_per_page]):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to PIL Image for processing
                    pil_image = Image.open(BytesIO(image_bytes))
                    
                    # Resize large images to reduce token usage
                    max_size = 1024
                    if pil_image.width > max_size or pil_image.height > max_size:
                        pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    # Convert to JPEG and base64
                    buffer = BytesIO()
                    pil_image.convert('RGB').save(buffer, format='JPEG', quality=85)
                    image_base64 = base64.b64encode(buffer.getvalue()).decode()
                    
                    page_images[page_num + 1].append(image_base64)
                    
                except Exception as e:
                    print(f"Error extracting image {img_index} from page {page_num + 1}: {e}")
                    continue
        
        doc.close()
        return page_images
        
    except Exception as e:
        print(f"Error extracting images from PDF: {e}")
        return {}

def process_pdf(pdf_path: str, chunk_size: int = 1000, overlap: int = 200) -> tuple[List[Dict[str, Any]], Dict[int, List[str]]]:
    """
    Reads a PDF and returns text chunks with page numbers AND extracted images.
    
    Args:
        pdf_path: Path to the PDF file
        chunk_size: Target size for each chunk (characters)
        overlap: Number of characters to overlap between chunks
    
    Returns:
        Tuple of (text_documents, page_images)
        - text_documents: List of dictionaries containing text chunks and page numbers
        - page_images: Dictionary mapping page numbers to lists of base64 images
    """
    # Extract images
    page_images = extract_images_from_pdf(pdf_path)
    
    # Extract text
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
            # If no text but has images, add a placeholder
            if page_num in page_images and page_images[page_num]:
                documents.append({
                    "text": f"[Page {page_num} contains images but no extractable text]",
                    "page": page_num,
                    "has_images": True
                })
            continue

        text = clean_text(text)
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                if len(current_chunk.strip()) >= 100:
                    documents.append({
                        "text": current_chunk.strip(),
                        "page": page_num,
                        "has_images": page_num in page_images and len(page_images[page_num]) > 0
                    })
                # Start new chunk with overlap
                words = current_chunk.split()
                overlap_words = words[-int(overlap/5):] if len(words) > overlap/5 else words
                current_chunk = " ".join(overlap_words) + " " + sentence + " "
            else:
                current_chunk += sentence + " "
        
        # Add remaining text
        if len(current_chunk.strip()) >= 100:
            documents.append({
                "text": current_chunk.strip(),
                "page": page_num,
                "has_images": page_num in page_images and len(page_images[page_num]) > 0
            })

    if not documents:
        raise Exception("No text or images could be extracted from the PDF")
    
    return documents, page_images