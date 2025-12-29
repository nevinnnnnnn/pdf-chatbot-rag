import os
import streamlit as st
from core.pdf_processor import process_pdf
from core.embeddings import create_vector_store
from core.qa_engine import answer_question

UPLOAD_DIR = "data/uploads"
VECTOR_DIR = "data/vectorstore"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)

st.set_page_config(page_title="PDF Chatbot", layout="centered")
st.title("📄 PDF Chatbot")

# ---------------- SESSION STATE ----------------
if "chat" not in st.session_state:
    st.session_state.chat = []

if "indexed" not in st.session_state:
    st.session_state.indexed = False

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file:
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    with st.spinner("Processing PDF..."):
        documents = process_pdf(file_path)
        create_vector_store(documents, VECTOR_DIR)

    st.session_state.indexed = True
    st.success("PDF processed successfully!")

# ---------------- CHAT UI ----------------
if st.session_state.indexed:
    user_input = st.chat_input("Ask a question about the PDF")

    if user_input:
        st.session_state.chat.append(("user", user_input))

        response = answer_question(
            question=user_input,
            vector_store_path=VECTOR_DIR
        )

        st.session_state.chat.append(("assistant", response["answer"]))

# Display chat
for role, message in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(message)