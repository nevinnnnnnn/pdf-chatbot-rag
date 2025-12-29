from pypdf import PdfReader
import re


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def process_pdf(pdf_path: str, chunk_size=500, overlap=50):
    reader = PdfReader(pdf_path)
    documents = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue

        text = clean_text(text)

        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            documents.append({
                "text": chunk,
                "page": page_num
            })

    return documents