import streamlit as st
import os
import pickle
import pandas as pd
from datetime import datetime
from core.auth import require_auth
from core.database import (
    create_user, get_all_users, update_user, delete_user,
    add_pdf, get_all_pdfs, delete_pdf, get_chat_history
)
from core.pdf_processor import process_pdf
from core.embeddings import create_vector_store

# Load CSS
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

st.set_page_config(page_title="Admin Panel", page_icon="👨‍💼", layout="wide")

# Require admin authentication
require_auth(required_role="admin")

user = st.session_state.user

# Sidebar
with st.sidebar:
    st.markdown(f"""
        <div class='user-info-card'>
            <div class='user-info-label'>Admin Dashboard</div>
            <div class='user-info-name'>{user['username']}</div>
            <div class='user-info-role'>{user['role']}</div>
        </div>
    """, unsafe_allow_html=True)

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
            st.info(f"""
                **File:** {uploaded_file.name}  
                **Size:** {uploaded_file.size / 1024 / 1024:.2f} MB
            """)
            
            if st.button("🚀 Upload and Index", type="primary", use_container_width=True):
                try:
                    with st.spinner("📄 Processing PDF..."):
                        # Save PDF
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_filename = f"{timestamp}_{uploaded_file.name.replace(' ', '_')}"
                        pdf_path = f"data/uploads/{safe_filename}"
                        
                        os.makedirs("data/uploads", exist_ok=True)
                        with open(pdf_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Process PDF
                        docs, page_images = process_pdf(pdf_path)
                        
                        if not docs:
                            st.error("❌ No text could be extracted from this PDF")
                        else:
                            # Create vector store
                            vector_path = f"data/vectorstore/{safe_filename.replace('.pdf', '')}"
                            with st.spinner(f"⚡ Indexing {len(docs)} chunks..."):
                                create_vector_store(docs, vector_path)
                            
                            # Save images
                            total_images = 0
                            if page_images:
                                images_path = os.path.join(vector_path, "images.pkl")
                                with open(images_path, "wb") as f:
                                    pickle.dump(page_images, f)
                                total_images = sum(len(imgs) for imgs in page_images.values())
                            
                            # Add to database
                            pdf_id = add_pdf(
                                filename=safe_filename,
                                original_name=uploaded_file.name,
                                uploaded_by=user['id'],
                                file_size=uploaded_file.size,
                                num_pages=len(set(d['page'] for d in docs)),
                                num_chunks=len(docs),
                                num_images=total_images
                            )
                            
                            st.success(f"""
                                ✅ **PDF Uploaded Successfully!**
                                
                                - 📄 **Chunks:** {len(docs)}
                                - 🖼️ **Images:** {total_images}
                                - 📊 **Pages:** {len(set(d['page'] for d in docs))}
                                - 🆔 **PDF ID:** {pdf_id}
                            """)
                            
                            st.balloons()
                
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
                            st.rerun()
                        else:
                            st.error("❌ Username or email already exists")
                else:
                    st.warning("⚠️ Please fill all fields")
    
    with col2:
        st.markdown("#### 📋 User List")
        
        # Get users created by this admin (or all if superadmin)
        if user['role'] == 'superadmin':
            users = get_all_users()
        else:
            users = get_all_users(role_filter='user')
        
        if users:
            # Filter out superadmin from admin view
            if user['role'] == 'admin':
                users = [u for u in users if u['role'] != 'superadmin']
            
            df = pd.DataFrame(users)
            df['is_active'] = df['is_active'].map({1: '✅ Active', 0: '❌ Inactive'})
            df['last_login'] = pd.to_datetime(df['last_login']).dt.strftime('%Y-%m-%d %H:%M')
            df = df[['username', 'email', 'role', 'is_active', 'last_login']]
            
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
                user_to_modify = st.selectbox(
                    "Select User",
                    options=[u['username'] for u in users],
                    key="modify_user"
                )
            
            with col_b:
                action = st.selectbox(
                    "Action",
                    options=["Deactivate", "Activate", "Delete"],
                    key="user_action"
                )
            
            with col_c:
                if st.button("Execute", type="primary", use_container_width=True):
                    selected_user = next(u for u in users if u['username'] == user_to_modify)
                    
                    if action == "Deactivate":
                        update_user(selected_user['id'], is_active=False)
                        st.success(f"✅ User '{user_to_modify}' deactivated")
                        st.rerun()
                    elif action == "Activate":
                        update_user(selected_user['id'], is_active=True)
                        st.success(f"✅ User '{user_to_modify}' activated")
                        st.rerun()
                    elif action == "Delete":
                        delete_user(selected_user['id'])
                        st.success(f"✅ User '{user_to_modify}' deleted")
                        st.rerun()
        else:
            st.info("📭 No users found. Create your first user above!")

# ==================== TAB 3: MANAGE PDFs ====================
with tab3:
    st.markdown("### 📚 PDF Library")
    
    # Get PDFs uploaded by this admin
    if user['role'] == 'superadmin':
        pdfs = get_all_pdfs()
    else:
        pdfs = get_all_pdfs(uploaded_by=user['id'])
    
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
            total_pages = sum(p['num_pages'] for p in pdfs)
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>Total Pages</div>
                </div>
            """.format(total_pages), unsafe_allow_html=True)
        
        with col3:
            total_chunks = sum(p['num_chunks'] for p in pdfs)
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>Total Chunks</div>
                </div>
            """.format(total_chunks), unsafe_allow_html=True)
        
        with col4:
            total_images = sum(p['num_images'] for p in pdfs)
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>Total Images</div>
                </div>
            """.format(total_images), unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 📋 PDF List")
        
        # Display PDFs
        df = pd.DataFrame(pdfs)
        df['file_size'] = df['file_size'].apply(lambda x: f"{x / 1024 / 1024:.2f} MB")
        df['upload_date'] = pd.to_datetime(df['upload_date']).dt.strftime('%Y-%m-%d %H:%M')
        df = df[['original_name', 'uploader_name', 'num_pages', 'num_chunks', 'num_images', 'file_size', 'upload_date']]
        
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
            pdf_to_delete = st.selectbox(
                "Select PDF to delete",
                options=[p['original_name'] for p in pdfs]
            )
        
        with col2:
            if st.button("🗑️ Delete", type="primary", use_container_width=True):
                selected_pdf = next(p for p in pdfs if p['original_name'] == pdf_to_delete)
                delete_pdf(selected_pdf['id'])
                st.success(f"✅ PDF '{pdf_to_delete}' deleted")
                st.rerun()
    else:
        st.info("📭 No PDFs uploaded yet. Upload your first PDF in the 'Upload PDF' tab!")

# ==================== TAB 4: ANALYTICS ====================
with tab4:
    st.markdown("### 📊 Analytics Dashboard")
    
    # Get chat history
    if user['role'] == 'superadmin':
        chats = get_chat_history(limit=100)
    else:
        # Get chats from users created by this admin (simplified - show all for now)
        chats = get_chat_history(limit=100)
    
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
            unique_users = len(set(c['user_id'] for c in chats))
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>Active Users</div>
                </div>
            """.format(unique_users), unsafe_allow_html=True)
        
        with col3:
            unique_pdfs = len(set(c['pdf_id'] for c in chats if c['pdf_id']))
            st.markdown("""
                <div class='stat-card'>
                    <div class='stat-value'>{}</div>
                    <div class='stat-label'>PDFs Queried</div>
                </div>
            """.format(unique_pdfs), unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 📜 Recent Activity")
        
        # Display recent chats
        df = pd.DataFrame(chats[:20])  # Show last 20
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        df = df[['username', 'pdf_name', 'question', 'timestamp']]
        df['question'] = df['question'].str[:100] + '...'
        
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