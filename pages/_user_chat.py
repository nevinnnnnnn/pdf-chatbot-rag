import streamlit as st
import os
import time
import sys
from typing import Dict, Any

# Add path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.auth import check_authentication
    from core.database import get_all_pdfs, log_chat
    from core.qa_engine import answer_question
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# ------------------------------------
# Page Configuration
# ------------------------------------
st.set_page_config(
    page_title="DocChat AI - Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------
# Load CSS
# ------------------------------------
css_loaded = False
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        css_loaded = True
except FileNotFoundError:
    # Fallback minimal CSS for light theme
    st.markdown("""
    <style>
    /* Light theme fallback CSS */
    :root {
        --primary: #2563eb;
        --primary-dark: #1e40af;
        --primary-light: #3b82f6;
        --primary-ultralight: #eff6ff;
        --bg-main: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-tertiary: #f1f5f9;
        --text-primary: #1e293b;
        --text-secondary: #475569;
        --text-muted: #64748b;
        --border-light: #e2e8f0;
        --border-blue: #93c5fd;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-main) !important;
        color: var(--text-primary) !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-light) !important;
    }
    
    .user-info-card {
        background-color: white !important;
        border: 1px solid var(--border-light);
        border-radius: 12px;
        padding: 20px;
        margin: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .user-info-label {
        color: var(--text-muted);
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    
    .user-info-name {
        color: var(--text-primary) !important;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    
    .user-info-role {
        color: var(--primary-dark) !important;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        background-color: var(--primary-ultralight);
        padding: 4px 10px;
        border-radius: 20px;
        display: inline-block;
    }
    
    .stButton button {
        background-color: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin: 4px 0 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton button:hover {
        background-color: var(--primary-dark) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    
    .page-title {
        color: var(--text-primary) !important;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 16px;
    }
    
    .page-subtitle {
        color: var(--text-secondary) !important;
        font-size: 16px;
        margin-bottom: 24px;
    }
    
    /* Ensure all text is visible */
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: var(--text-primary) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------
# Authentication Check
# ------------------------------------
def require_auth():
    """Check if user is authenticated"""
    if "user" not in st.session_state or not st.session_state.user:
        st.warning("Please login to access this page")
        if st.button("Go to Login"):
            st.switch_page("app.py")
        st.stop()
    
    user = st.session_state.user
    if user["role"] not in ["user", "admin", "superadmin"]:
        st.error("You don't have permission to access this page")
        st.stop()
    
    return user

# Check authentication
user = require_auth()

# ------------------------------------
# Session State Initialization
# ------------------------------------
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "selected_pdf_id" not in st.session_state:
    st.session_state.selected_pdf_id = None

if "selected_pdf" not in st.session_state:
    st.session_state.selected_pdf = None

# ------------------------------------
# Sidebar
# ------------------------------------
with st.sidebar:
    # User info card
    st.markdown(f"""
        <div class='user-info-card'>
            <div class='user-info-label'>Logged in as</div>
            <div class='user-info-name'>{user['username']}</div>
            <div class='user-info-role'>{user['role']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Navigation buttons
    if st.button("🏠 Home", use_container_width=True, key="home_btn"):
        st.switch_page("app.py")
    
    if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
        # Clear session and redirect to login
        st.session_state.clear()
        st.switch_page("app.py")
    
    st.divider()
    
    # PDF Selection
    st.markdown("### 📚 Available PDFs")
    
    try:
        pdfs = get_all_pdfs()
    except Exception as e:
        st.error(f"Error loading PDFs: {e}")
        pdfs = []
    
    if not pdfs:
        st.info("📭 No PDFs available yet. Please contact your admin.")
    else:
        try:
            pdf_options = {
                f"{pdf.get('original_name', 'Unknown')}": pdf["id"]
                for pdf in pdfs
            }
            
            selected_pdf_name = st.selectbox(
                "Select a PDF",
                options=list(pdf_options.keys()),
                key="pdf_selector",
                label_visibility="collapsed"
            )
            
            selected_pdf_id = pdf_options[selected_pdf_name]
            selected_pdf = next(p for p in pdfs if p["id"] == selected_pdf_id)
        except Exception as e:
            st.error(f"Error loading PDF details: {e}")
            selected_pdf = None
            selected_pdf_id = None
        
        # Handle PDF change
        if selected_pdf and st.session_state.selected_pdf_id != selected_pdf_id:
            st.session_state.selected_pdf_id = selected_pdf_id
            st.session_state.selected_pdf = selected_pdf
            st.session_state.chat_messages = []
            st.rerun()
        
        if selected_pdf:
            # PDF Info Card
            st.markdown("---")
            st.markdown("### 📄 Document Info")
            
            # Create info card
            info_col1, info_col2 = st.columns([2, 1])
            
            with info_col1:
                st.markdown(f"**{selected_pdf.get('original_name', 'Unknown')}**")
                st.caption(f"Uploaded by: {selected_pdf.get('uploader_name', 'Unknown')}")
            
            with info_col2:
                st.metric("Pages", selected_pdf.get('num_pages', 0))
            
            # Additional info in expander
            with st.expander("View Details"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Chunks", selected_pdf.get('num_chunks', 0))
                with col2:
                    st.metric("Images", selected_pdf.get('num_images', 0))
                with col3:
                    file_size_mb = selected_pdf.get('file_size', 0) / 1024 / 1024
                    st.metric("Size", f"{file_size_mb:.2f} MB")
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat_btn"):
        st.session_state.chat_messages = []
        st.success("Chat cleared!")
        time.sleep(0.5)
        st.rerun()

# ------------------------------------
# Main Content Area
# ------------------------------------
# Page Header
st.markdown("""
    <div class='page-header'>
        <h1 class='page-title'>💬 Document Chat</h1>
        <p class='page-subtitle'>Ask questions and get instant answers from your PDFs</p>
    </div>
""", unsafe_allow_html=True)

# Check if PDFs are available
if not pdfs:
    st.warning("""
    ## 📭 No PDFs Available
    
    There are no PDFs uploaded to the system yet. Please:
    
    1. **Contact your administrator** to upload PDFs
    2. **If you're an admin**, go to the Admin Panel to upload PDFs
    
    You can access the Admin Panel from the home page.
    """)
    
    if user["role"] in ["admin", "superadmin"]:
        if st.button("Go to Admin Panel", type="primary"):
            st.switch_page("pages/_admin_panel.py")
    
    st.stop()

# Check if PDF is selected
if not st.session_state.selected_pdf:
    st.info("👈 **Please select a PDF from the sidebar to start chatting**")
    
    # Show available PDFs in main area
    st.markdown("### Available Documents:")
    
    for pdf in pdfs[:5]:  # Show first 5 PDFs
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{pdf.get('original_name', 'Unknown')}**")
                st.caption(f"Uploaded by: {pdf.get('uploader_name', 'Unknown')}")
            with col2:
                if st.button("Select", key=f"select_{pdf['id']}"):
                    st.session_state.selected_pdf_id = pdf["id"]
                    st.session_state.selected_pdf = pdf
                    st.session_state.chat_messages = []
                    st.rerun()
            st.divider()
    
    if len(pdfs) > 5:
        st.info(f"... and {len(pdfs) - 5} more PDFs in the sidebar")
    
    st.stop()

# ------------------------------------
# Chat Interface
# ------------------------------------
selected_pdf = st.session_state.selected_pdf

# Show PDF info at top
st.markdown(f"""
    <div style='background-color: #f8fafc; padding: 16px; border-radius: 8px; border-left: 4px solid #2563eb; margin-bottom: 24px;'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <strong>📄 {selected_pdf.get('original_name', 'Unknown')}</strong>
                <div style='font-size: 14px; color: #64748b; margin-top: 4px;'>
                    {selected_pdf.get('num_pages', 0)} pages • {selected_pdf.get('num_chunks', 0)} chunks • {selected_pdf.get('num_images', 0)} images
                </div>
            </div>
            <div style='font-size: 14px; color: #64748b;'>
                Uploaded by: {selected_pdf.get('uploader_name', 'Unknown')}
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Display chat messages
for msg in st.session_state.chat_messages:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    
    with st.chat_message(role, avatar="🧑" if role == "user" else "🤖"):
        st.markdown(content)
        
        # Show sources for assistant messages
        if role == "assistant" and msg.get("sources"):
            with st.expander("📚 View Sources"):
                for idx, src in enumerate(msg["sources"], 1):
                    st.markdown(f"**Source {idx}** • Page {src.get('page', 'N/A')}")
                    if src.get("text"):
                        st.caption(src["text"][:300] + "..." if len(src["text"]) > 300 else src["text"])
                    if src.get("has_images"):
                        st.caption("📷 Contains images")
                    if idx < len(msg["sources"]):
                        st.divider()

# Chat input
if prompt := st.chat_input(f"Ask a question about {selected_pdf.get('original_name', 'the document')}..."):
    # Add user message to chat
    st.session_state.chat_messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Display user message
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
    
    # Display assistant message with streaming effect
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        
        try:
            # Get vector store path
            filename = selected_pdf.get('filename', '').replace('.pdf', '')
            vector_path = f"data/vectorstore/{filename}"
            
            # Check if vector store exists
            if not os.path.exists(vector_path):
                error_msg = f"⚠️ Error: Vector store not found for this PDF. Path: {vector_path}"
                message_placeholder.markdown(error_msg)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "sources": []
                })
                st.stop()
            
            # Get answer from QA engine
            with st.spinner("Analyzing document..."):
                result: Dict[str, Any] = answer_question(
                    question=prompt,
                    vector_store_path=vector_path
                )
            
            answer = result.get("answer", "I couldn't find an answer in the document.")
            sources = result.get("sources", [])
            
            # Stream the response
            full_response = ""
            for chunk in answer.split():
                full_response += chunk + " "
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.02)
            
            message_placeholder.markdown(full_response)
            
            # Add assistant message to chat history
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": sources
            })
            
            # Show sources if available
            if sources:
                with st.expander("📚 View Sources"):
                    for idx, src in enumerate(sources, 1):
                        st.markdown(f"**Source {idx}** • Page {src.get('page', 'N/A')}")
                        if src.get("text"):
                            st.caption(src["text"][:300] + "..." if len(src["text"]) > 300 else src["text"])
                        if src.get("has_images"):
                            st.caption("📷 Contains images")
                        if idx < len(sources):
                            st.divider()
            
            # Log the chat
            try:
                log_chat(
                    user_id=user["id"],
                    pdf_id=st.session_state.selected_pdf_id,
                    question=prompt,
                    answer=full_response[:500]  # Limit for logging
                )
            except Exception as log_error:
                st.warning(f"Note: Chat was not logged due to an error: {str(log_error)[:100]}")
        
        except Exception as e:
            error_msg = f"⚠️ Error: {str(e)}"
            message_placeholder.markdown(error_msg)
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": error_msg,
                "sources": []
            })

# Empty state when no messages
if not st.session_state.chat_messages:
    st.markdown("""
    <div style='text-align: center; padding: 60px 20px; color: #64748b;'>
        <div style='font-size: 48px; margin-bottom: 20px;'>💬</div>
        <h3 style='color: #475569;'>Start a conversation</h3>
        <p>Ask questions about the selected PDF to get started.</p>
        <div style='margin-top: 30px;'>
            <div style='display: inline-block; background-color: #f1f5f9; padding: 12px 20px; border-radius: 8px; margin: 5px;'>
                "What is this document about?"
            </div>
            <div style='display: inline-block; background-color: #f1f5f9; padding: 12px 20px; border-radius: 8px; margin: 5px;'>
                "Summarize the main points"
            </div>
            <div style='display: inline-block; background-color: #f1f5f9; padding: 12px 20px; border-radius: 8px; margin: 5px;'>
                "Find information about..."
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------
# Footer
# ------------------------------------
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"👤 {user['username']} ({user['role']})")
with col2:
    st.caption(f"📄 {selected_pdf.get('original_name', 'Unknown')}")
with col3:
    st.caption(f"💬 {len(st.session_state.chat_messages)} messages")