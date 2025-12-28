import os
import sys
import time
import streamlit as st

# Ensure project root is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.pdf_processor import process_pdf
from core.embeddings import create_vector_store
from core.qa_engine import answer_question

# ---------------- CONFIG ----------------

UPLOAD_DIR = "data/uploads"
VECTOR_DIR = "data/vectorstore"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)

st.set_page_config(
    page_title="PDF Chatbot",
    page_icon="📄",
    layout="centered"
)

st.title("📄 PDF Chatbot")
st.caption("Each chat has its own PDF knowledge base.")


# ---------------- SESSION STATE INIT ----------------

if "chats" not in st.session_state:
    st.session_state.chats = {"Chat 1": []}

if "active_chat" not in st.session_state:
    st.session_state.active_chat = "Chat 1"

if "chat_configs" not in st.session_state:
    st.session_state.chat_configs = {
        "Chat 1": {
            "pdf_path": None,
            "indexed": False
        }
    }


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.header("💬 Chats")

    if st.button("➕ New Chat"):
        chat_name = f"Chat {len(st.session_state.chats) + 1}"
        st.session_state.chats[chat_name] = []
        st.session_state.chat_configs[chat_name] = {
            "pdf_path": None,
            "indexed": False
        }
        st.session_state.active_chat = chat_name

    st.session_state.active_chat = st.radio(
        "Select a chat",
        list(st.session_state.chats.keys()),
        index=list(st.session_state.chats.keys()).index(
            st.session_state.active_chat
        )
    )

    if st.button("🧹 Clear Current Chat"):
        st.session_state.chats[st.session_state.active_chat] = []

    st.divider()
    st.header("📄 Upload PDF")

    uploaded_file = st.file_uploader(
        "Upload a PDF for this chat",
        type=["pdf"],
        key=f"upload_{st.session_state.active_chat}"
    )

    if uploaded_file:
        chat_id = st.session_state.active_chat.replace(" ", "_").lower()
        pdf_path = os.path.join(UPLOAD_DIR, f"{chat_id}_{uploaded_file.name}")
        vector_path = os.path.join(VECTOR_DIR, chat_id)

        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Processing and indexing PDF..."):
            documents = process_pdf(pdf_path)
            create_vector_store(documents, save_path=vector_path)

        st.session_state.chat_configs[st.session_state.active_chat] = {
            "pdf_path": pdf_path,
            "indexed": True
        }

        st.session_state.chats[st.session_state.active_chat] = []

        st.success("PDF indexed successfully!")


# ---------------- CHAT VIEW ----------------

active_chat = st.session_state.active_chat
chat_config = st.session_state.chat_configs[active_chat]

# Render chat history
for msg in st.session_state.chats[active_chat]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant":
            if msg.get("confidence") is not None:
                st.caption(f"Confidence: {msg['confidence']}")

            if msg.get("sources"):
                with st.expander("Sources"):
                    for src in msg["sources"]:
                        st.write(f"Page {src['page']} (distance: {src['distance']})")


# ---------------- CHAT INPUT ----------------

if chat_config["indexed"]:
    user_input = st.chat_input("Ask a question about this PDF...")

    if user_input:
        # Store user message
        st.session_state.chats[active_chat].append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            placeholder = st.empty()

            response = answer_question(
                user_input,
                vector_store_path=os.path.join(
                    VECTOR_DIR,
                    active_chat.replace(" ", "_").lower()
                )
            )

            answer = response["answer"]
            sources = response.get("sources", [])
            confidence = response.get("confidence")

            rendered = ""
            for char in answer:
                rendered += char
                placeholder.markdown(rendered)
                time.sleep(0.008)

            if confidence is not None:
                st.caption(f"Confidence: {confidence}")

            if sources:
                with st.expander("Sources"):
                    for src in sources:
                        st.write(f"Page {src['page']} (distance: {src['distance']})")

        st.session_state.chats[active_chat].append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "confidence": confidence
        })

else:
    st.info("Upload a PDF to start chatting.")
