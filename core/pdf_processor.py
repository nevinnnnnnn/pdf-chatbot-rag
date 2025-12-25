from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def process_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    documents = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue

        chunks = splitter.split_text(text)

        for chunk in chunks:
            documents.append({
                "text": chunk,
                "page": page_number
            })

    return documents