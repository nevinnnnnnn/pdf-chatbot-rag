import streamlit as st
import os
import pickle
import pandas as pd
from datetime import datetime
import sys

# Add path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.auth import require_auth, check_authentication
    from core.database import (
        create_user, get_all_users, update_user, delete_user,
        add_pdf, get_all_pdfs, delete_pdf, get_chat_history
    )
    from core.pdf_processor import process_pdf
    from core.embeddings import create_vector_store
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# ------------------------------------
# Page Configuration
# ------------------------------------
st.set_page_config(
    page_title="DocChat AI - Admin",
    page_icon="👨‍💼",
    layout="wide"
)

# Load CSS
css_loaded = False
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        css_loaded = True
except FileNotFoundError:
    # Fallback minimal CSS
    st.markdown("""
    <style>
    .user-info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
    }
    .user-info-label {
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 5px;
    }
    .user-info-name {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .user-info-role {
        font-size: 12px;
        opacity: 0.8;
        text-transform: uppercase;
    }
    .page-header {
        padding: 20px 0 30px 0;
        margin-bottom: 20px;
    }
    .page-title {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .page-subtitle {
        font-size: 16px;
        color: #666;
        margin-bottom: 20px;
    }
    .stat-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        border: 1px solid rgba(37, 99, 235, 0.3);
    }
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .stat-label {
        font-size: 12px;
        opacity: 0.8;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------
# Authentication Check
# ------------------------------------
def require_auth_wrapper(required_role="admin"):
    """Wrapper for authentication check"""
    if "user" not in st.session_state or not st.session_state.user:
        st.warning("Please login to access this page")
        st.stop()
    
    user = st.session_state.user
    allowed_roles = {
        "admin": ["admin", "superadmin"],
        "superadmin": ["superadmin"]
    }
    
    if required_role not in allowed_roles or user["role"] not in allowed_roles[required_role]:
        st.error(f"You don't have permission to access this page. Required role: {required_role}")
        st.stop()
    
    return user

# Check authentication
user = require_auth_wrapper("admin")

# Sidebar
with st.sidebar:
    st.markdown(f"""
        <div class='user-info-card'>
            <div class='user-info-label'>Admin Dashboard</div>
            <div class='user-info-name'>{user['username']}</div>
            <div class='user-info-role'>{user['role']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Home button
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")

# Page Header
st.markdown("""
    <div class='page-header'>
        <div class='page-title'>👨‍💼 Admin Panel</div>
        <div class='page-subtitle'>Manage users, upload PDFs, and view analytics</div>
    </div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload PDF", "👥 Manage Users", "📚 Manage PDFs", "📊 Analytics"])

# ==================== TAB 1: UPLOAD PDF ====================
with tab1:
    st.markdown("### 📤 Upload New PDF")
    st.markdown("Upload PDF documents that users can query and analyze.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Maximum file size: 200MB"
        )
        
        if uploaded_file:
            file_size_mb = uploaded_file.size / 1024 / 1024
            if file_size_mb > 200:
                st.error("❌ File size exceeds 200MB limit")
            else:
                st.info(f"""
                    **File:** {uploaded_file.name}  
                    **Size:** {file_size_mb:.2f} MB
                """)
                
                if st.button("🚀 Upload and Index", type="primary", use_container_width=True):
                    try:
                        with st.spinner("📄 Processing PDF..."):
                            # Create directories if they don't exist
                            os.makedirs("data/uploads", exist_ok=True)
                            os.makedirs("data/vectorstore", exist_ok=True)
                            
                            # Save PDF
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            safe_filename = f"{timestamp}_{uploaded_file.name.replace(' ', '_')}"
                            pdf_path = f"data/uploads/{safe_filename}"
                            
                            with open(pdf_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # Process PDF
                            try:
                                docs, page_images = process_pdf(pdf_path)
                            except Exception as proc_error:
                                st.error(f"❌ PDF processing failed: {proc_error}")
                                st.stop()
                            
                            if not docs:
                                st.error("❌ No text could be extracted from this PDF")
                            else:
                                # Create vector store
                                vector_path = f"data/vectorstore/{safe_filename.replace('.pdf', '')}"
                                with st.spinner(f"⚡ Indexing {len(docs)} chunks..."):
                                    create_vector_store(docs, vector_path)
                                
                                # Save images if available
                                total_images = 0
                                if page_images:
                                    images_dir = os.path.join(vector_path, "images")
                                    os.makedirs(images_dir, exist_ok=True)
                                    images_path = os.path.join(vector_path, "images.pkl")
                                    try:
                                        with open(images_path, "wb") as f:
                                            pickle.dump(page_images, f)
                                        total_images = sum(len(imgs) for imgs in page_images.values())
                                    except Exception as img_error:
                                        st.warning(f"⚠️ Could not save images: {img_error}")
                                
                                # Add to database
                                try:
                                    pdf_id = add_pdf(
                                        filename=safe_filename,
                                        original_name=uploaded_file.name,
                                        uploaded_by=user['id'],
                                        file_size=uploaded_file.size,
                                        num_pages=len(set(d['page'] for d in docs if 'page' in d)),
                                        num_chunks=len(docs),
                                        num_images=total_images
                                    )
                                    
                                    st.success(f"""
                                        ✅ **PDF Uploaded Successfully!**
                                        
                                        - 📄 **Chunks:** {len(docs)}
                                        - 🖼️ **Images:** {total_images}
                                        - 📊 **Pages:** {len(set(d['page'] for d in docs if 'page' in d))}
                                        - 🆔 **PDF ID:** {pdf_id}
                                    """)
                                    
                                    st.balloons()
                                except Exception as db_error:
                                    st.error(f"❌ Database error: {db_error}")
                    
                    except Exception as e:
                        st.error(f"❌ Upload failed: {str(e)}")
    
    with col2:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                        padding: 24px; border-radius: 16px; border: 1px solid rgba(37, 99, 235, 0.3);'>
                <h4 style='color: #f1f5f9; margin-bottom: 16px;'>📋 Upload Guidelines</h4>
                <ul style='color: #cbd5e1; font-size: 14px; line-height: 1.8;'>
                    <li>Maximum size: 200MB</li>
                    <li>Supported format: PDF only</li>
                    <li>Text-based PDFs work best</li>
                    <li>Images will be analyzed automatically</li>
                    <li>Processing time: 30s - 2min</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

# ==================== TAB 2: MANAGE USERS ====================
with tab2:
    st.markdown("### 👥 User Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### ➕ Create New User")
        
        with st.form("create_user_form"):
            new_username = st.text_input("Username", placeholder="johndoe")
            new_email = st.text_input("Email", placeholder="john@example.com")
            new_password = st.text_input("Password", type="password", placeholder="Secure password")
            new_role = st.selectbox("Role", options=["user", "admin"] if user['role'] == "admin" else ["user"])
            
            submit = st.form_submit_button("Create User", type="primary", use_container_width=True)
            
            if submit:
                if new_username and new_email and new_password:
                    if len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        success = create_user(
                            username=new_username,
                            email=new_email,
                            password=new_password,
                            role=new_role,
                            created_by=user['id']
                        )
                        
                        if success:
                            st.success(f"✅ User '{new_username}' created successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Username or email already exists")
                else:
                    st.warning("⚠️ Please fill all fields")
    
    with col2:
        st.markdown("#### 📋 User List")
        
        try:
            if user['role'] == 'superadmin':
                users = get_all_users()
            else:
                users = get_all_users()
                # Filter for admin to see only users
                users = [u for u in users if u['role'] == 'user']
        except Exception as e:
            st.error(f"Error loading users: {e}")
            users = []
        
        if users:
            # Filter out superadmin from admin view
            if user['role'] == 'admin':
                users = [u for u in users if u['role'] != 'superadmin']
            
            # Create DataFrame with safe defaults
            user_data = []
            for u in users:
                user_data.append({
                    'username': u.get('username', 'Unknown'),
                    'email': u.get('email', 'Unknown'),
                    'role': u.get('role', 'user'),
                    'is_active': '✅ Active' if u.get('is_active', 0) == 1 else '❌ Inactive',
                    'last_login': pd.to_datetime(u.get('last_login', '1900-01-01')).strftime('%Y-%m-%d %H:%M') if u.get('last_login') else 'Never'
                })
            
            df = pd.DataFrame(user_data)
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "username": st.column_config.TextColumn("Username", width="medium"),
                    "email": st.column_config.TextColumn("Email", width="large"),
                    "role": st.column_config.TextColumn("Role", width="small"),
                    "is_active": st.column_config.TextColumn("Status", width="small"),
                    "last_login": st.column_config.TextColumn("Last Login", width="medium")
                }
            )
            
            st.markdown("---")
            st.markdown("#### 🔧 User Actions")
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                user_options = [u.get('username', 'Unknown') for u in users]
                if user_options:
                    user_to_modify = st.selectbox(
                        "Select User",
                        options=user_options,
                        key="modify_user"
                    )
                else:
                    st.info("No users available")
                    user_to_modify = None
            
            with col_b:
                action = st.selectbox(
                    "Action",
                    options=["Deactivate", "Activate", "Delete"],
                    key="user_action"
                )
            
            with col_c:
                if user_to_modify and st.button("Execute", type="primary", use_container_width=True):
                    selected_user = next((u for u in users if u.get('username') == user_to_modify), None)
                    
                    if selected_user:
                        try:
                            if action == "Deactivate":
                                update_user(selected_user['id'], is_active=False)
                                st.success(f"✅ User '{user_to_modify}' deactivated")
                                time.sleep(1)
                                st.rerun()
                            elif action == "Activate":
                                update_user(selected_user['id'], is_active=True)
                                st.success(f"✅ User '{user_to_modify}' activated")
                                time.sleep(1)
                                st.rerun()
                            elif action == "Delete":
                                delete_user(selected_user['id'])
                                st.success(f"✅ User '{user_to_modify}' deleted")
                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error executing action: {e}")
                    else:
                        st.error("User not found")
        else:
            st.info("📭 No users found. Create your first user above!")

# ==================== TAB 3: MANAGE PDFs ====================
with tab3:
    st.markdown("### 📚 PDF Library")
    
    # Get PDFs
    try:
        if user['role'] == 'superadmin':
            pdfs = get_all_pdfs()
        else:
            pdfs = get_all_pdfs(uploaded_by=user['id'])
    except Exception as e:
        st.error(f"Error loading PDFs: {e}")
        pdfs = []
    
    if pdfs:
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>Total PDFs</div>
                </div>
            """.format(len(pdfs)), unsafe_allow_html=True)
        
        with col2:
            total_pages = sum(p.get('num_pages', 0) for p in pdfs)
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>Total Pages</div>
                </div>
            """.format(total_pages), unsafe_allow_html=True)
        
        with col3:
            total_chunks = sum(p.get('num_chunks', 0) for p in pdfs)
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>Total Chunks</div>
                </div>
            """.format(total_chunks), unsafe_allow_html=True)
        
        with col4:
            total_images = sum(p.get('num_images', 0) for p in pdfs)
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>Total Images</div>
                </div>
            """.format(total_images), unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 📋 PDF List")
        
        # Prepare data for display
        pdf_data = []
        for p in pdfs:
            pdf_data.append({
                'original_name': p.get('original_name', 'Unknown'),
                'uploader_name': p.get('uploader_name', 'Unknown'),
                'num_pages': p.get('num_pages', 0),
                'num_chunks': p.get('num_chunks', 0),
                'num_images': p.get('num_images', 0),
                'file_size': f"{p.get('file_size', 0) / 1024 / 1024:.2f} MB",
                'upload_date': pd.to_datetime(p.get('upload_date', '1900-01-01')).strftime('%Y-%m-%d %H:%M')
            })
        
        df = pd.DataFrame(pdf_data)
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "original_name": st.column_config.TextColumn("Filename", width="large"),
                "uploader_name": st.column_config.TextColumn("Uploaded By", width="medium"),
                "num_pages": st.column_config.NumberColumn("Pages", width="small"),
                "num_chunks": st.column_config.NumberColumn("Chunks", width="small"),
                "num_images": st.column_config.NumberColumn("Images", width="small"),
                "file_size": st.column_config.TextColumn("Size", width="small"),
                "upload_date": st.column_config.TextColumn("Upload Date", width="medium")
            }
        )
        
        st.markdown("---")
        st.markdown("#### 🗑️ Delete PDF")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            pdf_names = [p.get('original_name', 'Unknown') for p in pdfs]
            if pdf_names:
                pdf_to_delete = st.selectbox(
                    "Select PDF to delete",
                    options=pdf_names,
                    key="delete_pdf_select"
                )
            else:
                st.info("No PDFs available")
                pdf_to_delete = None
        
        with col2:
            if pdf_to_delete and st.button("🗑️ Delete", type="primary", use_container_width=True):
                selected_pdf = next((p for p in pdfs if p.get('original_name') == pdf_to_delete), None)
                if selected_pdf:
                    try:
                        delete_pdf(selected_pdf['id'])
                        st.success(f"✅ PDF '{pdf_to_delete}' deleted")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting PDF: {e}")
    else:
        st.info("📭 No PDFs uploaded yet. Upload your first PDF in the 'Upload PDF' tab!")

# ==================== TAB 4: ANALYTICS ====================
with tab4:
    st.markdown("### 📊 Analytics Dashboard")
    
    # Get chat history
    try:
        chats = get_chat_history(limit=100)
    except Exception as e:
        st.warning(f"Note: Analytics data not available: {e}")
        chats = []
    
    if chats:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>Total Queries</div>
                </div>
            """.format(len(chats)), unsafe_allow_html=True)
        
        with col2:
            unique_users = len(set(c.get('user_id', '') for c in chats if c.get('user_id')))
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>Active Users</div>
                </div>
            """.format(unique_users), unsafe_allow_html=True)
        
        with col3:
            unique_pdfs = len(set(c.get('pdf_id', '') for c in chats if c.get('pdf_id')))
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>PDFs Queried</div>
                </div>
            """.format(unique_pdfs), unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 📜 Recent Activity")
        
        # Prepare chat data
        chat_data = []
        for c in chats[:20]:  # Show last 20
            chat_data.append({
                'username': c.get('username', 'Unknown'),
                'pdf_name': c.get('pdf_name', 'Unknown'),
                'question': (c.get('question', '')[:100] + '...') if c.get('question') else 'No question',
                'timestamp': pd.to_datetime(c.get('timestamp', '1900-01-01')).strftime('%Y-%m-%d %H:%M')
            })
        
        if chat_data:
            df = pd.DataFrame(chat_data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "username": st.column_config.TextColumn("User", width="small"),
                    "pdf_name": st.column_config.TextColumn("PDF", width="medium"),
                    "question": st.column_config.TextColumn("Question", width="large"),
                    "timestamp": st.column_config.TextColumn("Time", width="medium")
                }
            )
    else:
        st.info("📭 No activity yet. Users will appear here once they start asking questions!")