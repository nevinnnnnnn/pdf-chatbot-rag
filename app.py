import os
import time
import pickle
from typing import List, Dict, Any
import streamlit as st

# Custom imports
from core.pdf_processor import process_pdf  # type: ignore
from core.embeddings import create_vector_store  # type: ignore
from core.qa_engine import answer_question  # type: ignore

# Constants
UPLOAD_DIR = "data/uploads"
VECTOR_DIR = "data/vectorstore"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)

st.set_page_config(page_title="PDF Chatbot", page_icon="📄", layout="centered")
st.title("📄 PDF Chatbot with Vision 👁️")

# 1. Initialize Session State
if "chats" not in st.session_state:
    st.session_state["chats"] = {"Chat 1": []}
if "active_chat" not in st.session_state:
    st.session_state["active_chat"] = "Chat 1"
if "configs" not in st.session_state:
    st.session_state["configs"] = {"Chat 1": {"indexed": False}}
if "processed_files" not in st.session_state:
    st.session_state["processed_files"] = {}

# Sidebar Logic
with st.sidebar:
    st.header("💬 Chats")

    if st.button("➕ New Chat"):
        new_chat_name = f"Chat {len(st.session_state.chats) + 1}"
        st.session_state.chats[new_chat_name] = []
        st.session_state.configs[new_chat_name] = {"indexed": False}
        st.session_state.active_chat = new_chat_name
        st.rerun()

    # Radio selection for active chat
    chat_options = list(st.session_state.chats.keys())
    st.session_state.active_chat = st.radio(
        "Select Chat",
        options=chat_options,
        index=chat_options.index(st.session_state.active_chat)
    )

    st.divider()
    uploaded = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_uploader")

    if uploaded:
        # Create unique file identifier
        file_id = f"{st.session_state.active_chat}_{uploaded.name}_{uploaded.size}"
        
        # Only process if this exact file hasn't been processed for this chat
        if st.session_state.processed_files.get(st.session_state.active_chat) != file_id:
            safe_chat_id = str(st.session_state.active_chat).replace(" ", "_")
            pdf_path = os.path.join(UPLOAD_DIR, f"{safe_chat_id}.pdf")
            vector_path = os.path.join(VECTOR_DIR, safe_chat_id)

            try:
                with open(pdf_path, "wb") as f:
                    f.write(uploaded.getbuffer())

                with st.spinner("Processing PDF (extracting text and images)..."):
                    # Process PDF and extract images
                    docs, page_images = process_pdf(pdf_path)
                    
                    if not docs:
                        st.error("No text could be extracted from this PDF.")
                    else:
                        with st.spinner(f"Indexing {len(docs)} chunks..."):
                            create_vector_store(docs, vector_path)
                        
                        # Save images separately
                        if page_images:
                            images_path = os.path.join(vector_path, "images.pkl")
                            with open(images_path, "wb") as f:
                                pickle.dump(page_images, f)
                            
                            total_images = sum(len(imgs) for imgs in page_images.values())
                            st.success(f"✅ PDF indexed! ({len(docs)} text chunks, {total_images} images)")
                        else:
                            st.success(f"✅ PDF indexed! ({len(docs)} text chunks)")
                        
                        st.session_state.configs[st.session_state.active_chat]["indexed"] = True
                        st.session_state.processed_files[st.session_state.active_chat] = file_id
                        
            except Exception as e:
                st.error(f"Error processing PDF: {str(e)}")
                st.session_state.configs[st.session_state.active_chat]["indexed"] = False

# Main Chat Area
active_chat_name = str(st.session_state.active_chat)
history = st.session_state.chats[active_chat_name]
config = st.session_state.configs.get(active_chat_name, {"indexed": False})

# Display message history
for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Interaction logic
if config.get("indexed"):
    user_input = st.chat_input("Ask about your PDF (text or images)...")

    if user_input:
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Save to session_state
        st.session_state.chats[active_chat_name].append({"role": "user", "content": user_input})

        # Generate Assistant Response
        with st.chat_message("assistant"):
            placeholder = st.empty()
            
            safe_chat_id = active_chat_name.replace(" ", "_")
            
            try:
                result: Dict[str, Any] = answer_question(
                    user_input,
                    vector_store_path=os.path.join(VECTOR_DIR, safe_chat_id)
                )

                full_response = result.get("answer", "I couldn't find an answer.")
                
                # Streaming effect
                displayed_text = ""
                for word in full_response.split():
                    displayed_text += word + " "
                    placeholder.markdown(displayed_text + "▌")
                    time.sleep(0.02)
                placeholder.markdown(full_response)
                
                # Show if vision was used
                if result.get("used_vision"):
                    st.caption("👁️ Analyzed with vision model (images included)")
                
                # Display sources if available
                if result.get("sources"):
                    with st.expander("📚 Sources"):
                        for idx, source in enumerate(result["sources"], 1):
                            st.write(f"**Source {idx}** (Page {source['page']}):")
                            st.write(source['text'][:200] + "...")
                            if source.get('has_images'):
                                st.caption("📷 This page contains images")
                            st.write(f"_Relevance score: {source.get('distance', 'N/A')}_")
                            st.divider()

            except Exception as e:
                full_response = f"Error: {str(e)}"
                placeholder.markdown(full_response)

        # Save assistant response to session_state
        st.session_state.chats[active_chat_name].append({
            "role": "assistant",
            "content": full_response
        })
        
        # Force rerun to clear the input box
        st.rerun()
else:
    st.info("👈 Please upload and index a PDF in the sidebar to start chatting.")
    st.caption("✨ Now with vision support for images, charts, and diagrams!")