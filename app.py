import os
import time
from typing import List, Dict, Any
import streamlit as st

# Custom imports - added type ignores for Pylance if these don't have stubs
from core.pdf_processor import process_pdf # type: ignore
from core.embeddings import create_vector_store # type: ignore
from core.qa_engine import answer_question # type: ignore

# Constants
UPLOAD_DIR = "data/uploads"
VECTOR_DIR = "data/vectorstore"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)

st.set_page_config(page_title="PDF Chatbot", page_icon="📄", layout="centered")
st.title("📄 PDF Chatbot")

# Initialize Session State with explicit types
if "chats" not in st.session_state:
    st.session_state["chats"] = {"Chat 1": []}
if "active_chat" not in st.session_state:
    st.session_state["active_chat"] = "Chat 1"
if "configs" not in st.session_state:
    st.session_state["configs"] = {"Chat 1": {"indexed": False}}

# Sidebar
with st.sidebar:
    st.header("💬 Chats")

    if st.button("➕ New Chat"):
        new_chat_name = f"Chat {len(st.session_state.chats) + 1}"
        st.session_state.chats[new_chat_name] = []
        st.session_state.configs[new_chat_name] = {"indexed": False}
        st.session_state.active_chat = new_chat_name
        st.rerun()

    # Radio selection for active chat
    st.session_state.active_chat = st.radio(
        "Select Chat", 
        options=list(st.session_state.chats.keys()),
        index=list(st.session_state.chats.keys()).index(st.session_state.active_chat)
    )

    st.divider()
    uploaded = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded:
        # Solution for "replace" on None: cast to string explicitly
        safe_chat_id = str(st.session_state.active_chat).replace(" ", "_")
        pdf_path = os.path.join(UPLOAD_DIR, f"{safe_chat_id}.pdf")
        vector_path = os.path.join(VECTOR_DIR, safe_chat_id)

        with open(pdf_path, "wb") as f:
            f.write(uploaded.getbuffer())

        with st.spinner("Indexing PDF..."):
            # Added type hints to satisfy Pylance warnings
            docs: List[Any] = process_pdf(pdf_path)
            create_vector_store(docs, vector_path)

        st.session_state.configs[st.session_state.active_chat]["indexed"] = True
        st.session_state.chats[st.session_state.active_chat] = []
        st.success("PDF indexed!")

# Main Chat Area
active_chat_name = str(st.session_state.active_chat)
messages = st.session_state.chats.get(active_chat_name, [])
config = st.session_state.configs.get(active_chat_name, {"indexed": False})

# Display message history
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Interaction logic
if config.get("indexed"):
    user_input = st.chat_input("Ask something about your PDF...")

    if user_input:
        # Add user message to UI and State
        with st.chat_message("user"):
            st.markdown(user_input)
        messages.append({"role": "user", "content": user_input})

        # Generate Assistant Response
        with st.chat_message("assistant"):
            placeholder = st.empty()
            
            # Fetch response
            safe_chat_id = active_chat_name.replace(" ", "_")
            result: Dict[str, Any] = answer_question(
                user_input,
                vector_store_path=os.path.join(VECTOR_DIR, safe_chat_id)
            )

            # Streaming effect
            full_response = result.get("answer", "I couldn't find an answer.")
            displayed_text = ""
            for word in full_response.split():
                displayed_text += word + " "
                placeholder.markdown(displayed_text + "▌")
                time.sleep(0.02)
            placeholder.markdown(full_response)

        # Update State with assistant response
        messages.append({
            "role": "assistant",
            "content": full_response,
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0)
        })
else:
    st.info("Please upload and index a PDF in the sidebar to start chatting.")