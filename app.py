import os
import streamlit as st
from typing import Dict, List, TypedDict

from core.pdf_processor import process_pdf
from core.embeddings import create_vector_store
from core.qa_engine import answer_question


# -----------------------------
# Types
# -----------------------------
class ChatMessage(TypedDict):
    role: str
    content: str


# -----------------------------
# Config
# -----------------------------
UPLOAD_DIR = "data/uploads"
VECTOR_DIR = "data/vectorstore"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)

st.set_page_config(page_title="PDF Chatbot", layout="centered")
st.title("📄 PDF Chatbot")

# -----------------------------
# Session State Initialization
# -----------------------------
if "chats" not in st.session_state:
    st.session_state.chats: Dict[str, List[ChatMessage]] = {
        "Chat 1": []
    }

if "active_chat" not in st.session_state:
    st.session_state.active_chat = "Chat 1"

if "chat_config" not in st.session_state:
    st.session_state.chat_config: Dict[str, Dict[str, bool]] = {
        "Chat 1": {"indexed": False}
    }

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("Chats")

    if st.button("➕ New Chat"):
        name = f"Chat {len(st.session_state.chats) + 1}"
        st.session_state.chats[name] = []
        st.session_state.chat_config[name] = {"indexed": False}
        st.session_state.active_chat = name

    st.session_state.active_chat = st.radio(
        "Select Chat",
        list(st.session_state.chats.keys()),
        index=list(st.session_state.chats.keys()).index(st.session_state.active_chat),
    )

    st.divider()
    st.header("Upload PDF")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file:
        pdf_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Processing PDF..."):
            docs = process_pdf(pdf_path)
            create_vector_store(docs, VECTOR_DIR)

        st.session_state.chat_config[st.session_state.active_chat]["indexed"] = True
        st.success("PDF indexed successfully!")

# -----------------------------
# Chat UI
# -----------------------------
active_chat = st.session_state.active_chat

for msg in st.session_state.chats[active_chat]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.chat_config[active_chat]["indexed"]:
    user_input = st.chat_input("Ask something about the PDF...")

    if user_input:
        st.session_state.chats[active_chat].append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):
            st.markdown(user_input)

        history = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}"
            for m in st.session_state.chats[active_chat][-6:]
        )

        with st.chat_message("assistant"):
            response = answer_question(
                question=user_input,
                vector_store_path=VECTOR_DIR,
                chat_history=history
            )

            st.markdown(response["answer"])

        st.session_state.chats[active_chat].append({
            "role": "assistant",
            "content": response["answer"]
        })

else:
    st.info("Upload a PDF to start chatting.")