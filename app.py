import os
import time
import pickle
from typing import List, Dict, Any
import streamlit as st

# Custom imports
from core.pdf_processor import process_pdf
from core.embeddings import create_vector_store
from core.qa_engine import answer_question

# Constants
UPLOAD_DIR = "data/uploads"
VECTOR_DIR = "data/vectorstore"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)

# Page Configuration
st.set_page_config(
    page_title="ChatGPT 5.2",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    try:
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

load_css()

# Initialize Session State
if "chats" not in st.session_state:
    st.session_state["chats"] = {"New chat": []}
if "active_chat" not in st.session_state:
    st.session_state["active_chat"] = "New chat"
if "configs" not in st.session_state:
    st.session_state["configs"] = {"New chat": {"indexed": False}}
if "processed_files" not in st.session_state:
    st.session_state["processed_files"] = {}

# Sidebar
with st.sidebar:
    # Header with Logo
    st.markdown("""
        <div class='sidebar-title'>
            <span style='font-size: 24px;'>⚡</span>
            <span>ChatGPT 5.2</span>
        </div>
    """, unsafe_allow_html=True)
    
    # New Chat Button
    if st.button("🖊️ New chat", use_container_width=True):
        chat_count = len([k for k in st.session_state.chats.keys()])
        new_chat_name = f"Chat {chat_count + 1}"
        st.session_state.chats[new_chat_name] = []
        st.session_state.configs[new_chat_name] = {"indexed": False}
        st.session_state.active_chat = new_chat_name
        st.rerun()
    
    # Section dividers
    st.markdown("<div class='sidebar-section-header'>YOUR CHATS</div>", unsafe_allow_html=True)
    
    # Chat Selection
    chat_options = list(st.session_state.chats.keys())
    selected_chat = st.radio(
        "Select Chat",
        options=chat_options,
        index=chat_options.index(st.session_state.active_chat),
        label_visibility="collapsed"
    )
    
    if selected_chat != st.session_state.active_chat:
        st.session_state.active_chat = selected_chat
        st.rerun()
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-section-header'>📄 DOCUMENT</div>", unsafe_allow_html=True)
    
    # PDF Upload
    uploaded = st.file_uploader(
        "Drag & drop PDF",
        type=["pdf"],
        label_visibility="collapsed"
    )
    
    if uploaded:
        file_id = f"{st.session_state.active_chat}_{uploaded.name}_{uploaded.size}"
        
        if st.session_state.processed_files.get(st.session_state.active_chat) != file_id:
            safe_chat_id = str(st.session_state.active_chat).replace(" ", "_")
            pdf_path = os.path.join(UPLOAD_DIR, f"{safe_chat_id}.pdf")
            vector_path = os.path.join(VECTOR_DIR, safe_chat_id)

            try:
                with open(pdf_path, "wb") as f:
                    f.write(uploaded.getbuffer())

                with st.spinner("Processing PDF..."):
                    docs, page_images = process_pdf(pdf_path)
                    
                    if not docs:
                        st.error("No text could be extracted")
                    else:
                        with st.spinner(f"Indexing {len(docs)} chunks..."):
                            create_vector_store(docs, vector_path)
                        
                        if page_images:
                            images_path = os.path.join(vector_path, "images.pkl")
                            with open(images_path, "wb") as f:
                                pickle.dump(page_images, f)
                            
                            total_images = sum(len(imgs) for imgs in page_images.values())
                            st.success(f"✅ {len(docs)} chunks, {total_images} images")
                        else:
                            st.success(f"✅ {len(docs)} chunks indexed")
                        
                        st.session_state.configs[st.session_state.active_chat]["indexed"] = True
                        st.session_state.processed_files[st.session_state.active_chat] = file_id
                        
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.configs[st.session_state.active_chat]["indexed"] = False
    
    # Document Status
    if st.session_state.configs.get(st.session_state.active_chat, {}).get("indexed"):
        st.markdown("""
            <div class='doc-status'>
                <div class='doc-status-label'>📄 DOCUMENT LOADED</div>
                <div class='doc-status-text'>Ready to answer</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class='doc-status'>
                <div class='doc-status-label'>No document</div>
                <div class='doc-status-text' style='color: #8e8e8e;'>Upload PDF above</div>
            </div>
        """, unsafe_allow_html=True)

# Main Chat Area
st.markdown("<div class='main-chat-container'>", unsafe_allow_html=True)

active_chat_name = str(st.session_state.active_chat)
history = st.session_state.chats[active_chat_name]
config = st.session_state.configs.get(active_chat_name, {"indexed": False})

# Welcome Screen
if len(history) == 0:
    st.markdown("""
        <div class='welcome-screen'>
                <h1>
            <div class='welcome-title'>UPLOAD A PDF AND KNOW MORE ABOUT IT!!</div>
                </h1>
        </div>
    """, unsafe_allow_html=True)

# Display Messages
for msg in history:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "⚡"):
        st.markdown(msg["content"])

st.markdown("</div>", unsafe_allow_html=True)

# Chat Input
if config.get("indexed"):
    user_input = st.chat_input("Ask anything")

    if user_input:
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)
        
        st.session_state.chats[active_chat_name].append({"role": "user", "content": user_input})

        with st.chat_message("assistant", avatar="⚡"):
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
                
                # Vision indicator
                if result.get("used_vision"):
                    st.caption("👁️ Analyzed with vision")
                
                # Sources
                if result.get("sources"):
                    with st.expander("📚 View sources"):
                        for idx, source in enumerate(result["sources"], 1):
                            st.markdown(f"**Source {idx}** • Page {source['page']}")
                            st.caption(source['text'][:150] + "...")
                            if source.get('has_images'):
                                st.caption("📷 Contains images")
                            if idx < len(result["sources"]):
                                st.divider()

            except Exception as e:
                full_response = f"⚠️ Error: {str(e)}"
                placeholder.markdown(full_response)

        st.session_state.chats[active_chat_name].append({
            "role": "assistant",
            "content": full_response
        })
        
        st.rerun()
else:
    st.chat_input("Upload a PDF document to start", disabled=True)