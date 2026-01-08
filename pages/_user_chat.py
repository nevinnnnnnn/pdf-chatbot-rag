import streamlit as st
import os
import time
import pickle
from typing import Dict, Any
from core.auth import require_auth
from core.database import get_all_pdfs, log_chat
from core.qa_engine import answer_question

# Load CSS
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

st.set_page_config(page_title="User Chat", page_icon="👤", layout="wide")

# Require authentication
require_auth()

user = st.session_state.user

# Sidebar
with st.sidebar:
    st.markdown(f"""
        <div class='user-info-card'>
            <div class='user-info-label'>Logged in as</div>
            <div class='user-info-name'>{user['username']}</div>
            <div class='user-info-role'>{user['role']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='sidebar-section-header'>📚 Available PDFs</div>", unsafe_allow_html=True)
    
    # Get available PDFs
    pdfs = get_all_pdfs()
    
    if pdfs:
        pdf_options = {f"{pdf['original_name']} (by {pdf['uploader_name']})": pdf['id'] for pdf in pdfs}
        selected_pdf_name = st.selectbox(
            "Select a PDF",
            options=list(pdf_options.keys()),
            label_visibility="collapsed"
        )
        selected_pdf_id = pdf_options[selected_pdf_name]
        
        # Find selected PDF details
        selected_pdf = next(p for p in pdfs if p['id'] == selected_pdf_id)
        
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                        padding: 20px; border-radius: 12px; margin-top: 16px;
                        border: 1px solid rgba(37, 99, 235, 0.3);'>
                <div style='color: #94a3b8; font-size: 11px; font-weight: 600; 
                           text-transform: uppercase; margin-bottom: 8px;'>📄 Document Info</div>
                <div style='color: #f1f5f9; font-size: 14px; font-weight: 600; margin-bottom: 4px;'>
                    {selected_pdf['original_name']}
                </div>
                <div style='color: #cbd5e1; font-size: 12px;'>
                    📄 {selected_pdf['num_pages']} pages<br>
                    📊 {selected_pdf['num_chunks']} chunks<br>
                    🖼️ {selected_pdf['num_images']} images<br>
                    👤 Uploaded by: {selected_pdf['uploader_name']}
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("📭 No PDFs available yet. Please contact your admin to upload documents.")
        st.stop()

# Main Chat Area
st.markdown("""
    <div class='page-header'>
        <div class='page-title'>💬 Chat with Documents</div>
        <div class='page-subtitle'>Ask questions and get instant answers from uploaded PDFs</div>
    </div>
""", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🤖"):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about the document..."):
    # Display user message
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        placeholder = st.empty()
        
        try:
            # Get vector store path
            vector_path = f"data/vectorstore/{selected_pdf['filename'].replace('.pdf', '')}"
            
            result: Dict[str, Any] = answer_question(
                prompt,
                vector_store_path=vector_path
            )
            
            full_response = result.get("answer", "I couldn't find an answer.")
            
            # Streaming effect
            displayed_text = ""
            for word in full_response.split():
                displayed_text += word + " "
                placeholder.markdown(displayed_text + "▌")
                time.sleep(0.02)
            placeholder.markdown(full_response)
            
            # Log chat
            log_chat(user['id'], selected_pdf_id, prompt, full_response)
            
            # Show vision indicator
            if result.get("used_vision"):
                st.caption("👁️ Analyzed with vision model")
            # Display sources
            if result.get("sources"):
                with st.expander("📚 View Sources"):
                    for idx, source in enumerate(result["sources"], 1):
                        st.markdown(f"**Source {idx}** • Page {source['page']}")
                        st.caption(source['text'][:200] + "...")
                        if source.get('has_images'):
                            st.caption("📷 Contains images")
                        if idx < len(result["sources"]):
                            st.divider()
        
        except Exception as e:
            full_response = f"⚠️ Error: {str(e)}"
            placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()