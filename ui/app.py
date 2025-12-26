import sys
import os
import base64
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import streamlit.components.v1 as components

from core.pdf_processor import process_pdf
from core.embeddings import create_vector_store
from core.qa_engine import answer_question

UPLOAD_DIR = "data/uploads"

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="PDF Chatbot",
    page_icon="📄",
    layout="centered"
)

st.title("PDF Chatbot")
st.caption("Ask questions strictly related to the uploaded PDF.")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------- Session State ----------------
st.session_state.setdefault("pdf_indexed", False)
st.session_state.setdefault("messages", [])
st.session_state.setdefault("dark_mode", False)
st.session_state.setdefault("pdf_path", None)

# ---------------- Dark Mode ----------------
if st.session_state.dark_mode:
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0f172a;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Controls")

    st.session_state.dark_mode = st.toggle(
        "Dark Mode", value=st.session_state.dark_mode
    )

    if st.button("Clear Chat"):
        st.session_state.messages = []

    st.divider()
    st.header("Upload PDF")

    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

    if uploaded_file:
        pdf_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

        if st.session_state.pdf_path != pdf_path:
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner("Processing and indexing PDF..."):
                documents = process_pdf(pdf_path)
                create_vector_store(documents)

            st.session_state.pdf_indexed = True
            st.session_state.pdf_path = pdf_path
            st.session_state.messages = []

            st.success("PDF indexed successfully!")

    if st.session_state.pdf_indexed:
        with open(st.session_state.pdf_path, "rb") as f:
            pdf_base64 = base64.b64encode(f.read()).decode()

        components.iframe(
            src=f"data:application/pdf;base64,{pdf_base64}",
            height=400
        )

# ---------------- Chat History ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant":
            if msg.get("confidence") is not None:
                st.caption(f"Confidence: {msg['confidence']}")

            if msg.get("sources"):
                with st.expander("Sources"):
                    for src in msg["sources"]:
                        st.write(f"Page {src['page']} (distance: {src['distance']})")

# ---------------- Chat Input ----------------
if st.session_state.pdf_indexed:
    user_input = st.chat_input("Ask a question about the PDF...")

    if user_input:
        #Render USER immediately
        with st.chat_message("user"):
            st.markdown(user_input)

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        #Render ASSISTANT once
        with st.chat_message("assistant"):
            placeholder = st.empty()

            response = answer_question(user_input)
            answer = response["answer"]
            sources = response.get("sources", [])
            confidence = response.get("confidence", None)

            typed = ""
            for char in answer:
                typed += char
                placeholder.markdown(typed)
                time.sleep(0.008)

            if confidence is not None:
                st.caption(f"Confidence: {confidence}")

            if sources:
                with st.expander("Sources"):
                    for src in sources:
                        st.write(f"Page {src['page']} (distance: {src['distance']})")

        #Store assistant AFTER rendering
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "confidence": confidence
        })
else:
    st.info("Upload a PDF from the sidebar to start chatting.")