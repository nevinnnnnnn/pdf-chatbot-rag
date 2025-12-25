import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

from core.pdf_processor import process_pdf
from core.embeddings import create_vector_store
from core.qa_engine import answer_question

UPLOAD_DIR = "data/uploads"

st.set_page_config(
    page_title="PDF Chatbot",
    page_icon="📄",
    layout="centered"
)

st.title("PDF Question Answering Chatbot")
st.write("Upload a PDF and ask questions based only on its content.")

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- PDF Upload ---
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    pdf_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

    # Save uploaded PDF
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success("PDF uploaded successfully!")

    # Process & index PDF
    with st.spinner("Processing and indexing document..."):
        documents = process_pdf(pdf_path)
        create_vector_store(documents)

    st.success("Document indexed. You can now ask questions!")
    st.divider()

    # --- Question Answering ---
    question = st.text_input("Ask a question about the document:")

    if question:
        with st.spinner("Thinking..."):
            response = answer_question(question)

        st.subheader("Answer")
        st.write(response["answer"])

        st.subheader("Sources")
        if response.get("sources"):
            for src in response["sources"]:
                st.write(f"Page {src['page']} (distance: {src['distance']})")
        else:
            st.write("No sources available.")