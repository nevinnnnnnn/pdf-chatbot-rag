"""
CHAT PDF - Professional Document AI Assistant
Clean & Minimal UI Version
"""

import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Dict

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Chat PDF | AI Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MINIMAL CSS
# ============================================================================

def load_minimal_css():
    """Load clean, light UI with proper contrast"""
    st.markdown("""
    <style>
    /* ========== GLOBAL STYLES ========== */
    :root {
        --primary-blue: #1e88e5;
        --light-blue: #e3f2fd;
        --medium-blue: #90caf9;
        --dark-blue: #1565c0;
        --text-dark: #1a237e;
        --text-medium: #283593;
        --text-light: #5c6bc0;
        --bg-white: #ffffff;
        --bg-light: #f8fafc;
        --border-light: #bbdefb;
        --success: #4caf50;
        --warning: #ff9800;
        --danger: #f44336;
    }
    
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        background-color: var(--bg-white);
        color: var(--text-dark);
    }
    
    /* ========== HIDE DEFAULT ELEMENTS ========== */
    #MainMenu, footer, header, .stDeployButton, [data-testid="stStatusWidget"] {
        visibility: hidden;
        display: none;
    }
    
    /* ========== TEXT ELEMENTS ========== */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-dark) !important;
        font-weight: 600;
    }
    
    p, span, div, label {
        color: var(--text-medium) !important;
    }
    
    .stMarkdown p, .stMarkdown span {
        color: var(--text-medium) !important;
    }
    
    /* ========== FORM ELEMENTS ========== */
    .stTextInput > div > div {
        background: var(--bg-white);
        border: 2px solid var(--border-light);
        border-radius: 8px;
        transition: all 0.2s;
    }
    
    .stTextInput > div > div:hover {
        border-color: var(--medium-blue);
        background: var(--light-blue);
    }
    
    .stTextInput > div > div:focus-within {
        border-color: var(--primary-blue);
        box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.1);
    }
    
    .stTextInput input {
        color: var(--text-dark) !important;
        font-size: 16px;
    }
    
    .stTextInput input::placeholder {
        color: var(--text-light) !important;
    }
    
    /* ========== BUTTONS ========== */
    .stButton > button {
        background-color: var(--primary-blue);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        font-size: 15px;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: var(--dark-blue);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.2);
    }
    
    .stButton > button[kind="secondary"] {
        background-color: transparent;
        border: 2px solid var(--primary-blue);
        color: var(--primary-blue) !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: var(--light-blue);
        border-color: var(--dark-blue);
        color: var(--dark-blue) !important;
    }
    
    /* ========== CARDS & CONTAINERS ========== */
    .clean-card {
        background: var(--bg-white);
        border: 2px solid var(--border-light);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
        transition: all 0.3s;
    }
    
    .clean-card:hover {
        border-color: var(--medium-blue);
        box-shadow: 0 6px 20px rgba(144, 202, 249, 0.15);
    }
    
    .metric-card {
        background: linear-gradient(135deg, var(--light-blue), #f0f7ff);
        border: 2px solid var(--border-light);
        border-radius: 12px;
        padding: 24px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: var(--text-dark);
        margin: 8px 0;
    }
    
    .metric-label {
        font-size: 14px;
        color: var(--text-medium);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* ========== SIDEBAR ========== */
    [data-testid="stSidebar"] {
        background-color: var(--bg-light);
        border-right: 2px solid var(--border-light);
    }
    
    .sidebar-header {
        text-align: center;
        padding: 32px 0 24px 0;
        border-bottom: 2px solid var(--border-light);
        margin-bottom: 24px;
    }
    
    .sidebar-header h2 {
        color: var(--text-dark) !important;
        margin: 0;
    }
    
    .sidebar-header p {
        color: var(--text-light) !important;
        margin: 4px 0 0 0;
    }
    
    /* ========== USER INFO CARD ========== */
    .user-info-card {
        background: white;
        border: 2px solid var(--border-light);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
    }
    
    .username {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-dark);
        margin-bottom: 4px;
    }
    
    .role-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        background: var(--light-blue);
        color: var(--primary-blue);
        border: 1px solid var(--medium-blue);
    }
    
    /* ========== NAVIGATION ========== */
    .nav-section {
        padding: 0 16px;
        margin-bottom: 32px;
    }
    
    .nav-section-title {
        font-size: 14px;
        color: var(--text-light);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 16px;
        padding-left: 8px;
    }
    
    /* ========== SECTION HEADERS ========== */
    .section-header {
        font-size: 20px;
        font-weight: 600;
        color: var(--text-dark);
        margin: 32px 0 20px 0;
        padding-bottom: 12px;
        border-bottom: 2px solid var(--border-light);
    }
    
    /* ========== TABLES ========== */
    .dataframe {
        border: 2px solid var(--border-light);
        border-radius: 8px;
        overflow: hidden;
    }
    
    .dataframe th {
        background-color: var(--light-blue);
        color: var(--text-dark);
        font-weight: 600;
        border-bottom: 2px solid var(--border-light);
    }
    
    .dataframe td {
        color: var(--text-medium);
        border-bottom: 1px solid var(--border-light);
    }
    
    /* ========== EXPANDERS ========== */
    .stExpander {
        border: 2px solid var(--border-light);
        border-radius: 8px;
        margin: 12px 0;
    }
    
    .stExpander summary {
        color: var(--text-dark);
        font-weight: 500;
        padding: 16px;
    }
    
    /* ========== ALERTS ========== */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
    }
    
    .stSuccess {
        background-color: #e8f5e9;
        border-left-color: var(--success);
        color: #2e7d32;
    }
    
    .stError {
        background-color: #ffebee;
        border-left-color: var(--danger);
        color: #c62828;
    }
    
    .stWarning {
        background-color: #fff3e0;
        border-left-color: var(--warning);
        color: #ef6c00;
    }
    
    .stInfo {
        background-color: var(--light-blue);
        border-left-color: var(--primary-blue);
        color: var(--text-dark);
    }
    
    /* ========== DIVIDERS ========== */
    hr {
        border: none;
        height: 2px;
        background: var(--border-light);
        margin: 24px 0;
    }
    
    /* ========== SCROLLBAR ========== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-light);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--medium-blue);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-blue);
    }
    
    /* ========== RESPONSIVE ========== */
    @media (max-width: 768px) {
        .metric-value {
            font-size: 24px;
        }
        
        .clean-card {
            padding: 16px;
        }
    }
    
    /* ========== FIX STREAMLIT CONTAINERS ========== */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Ensure all text is visible */
    .css-1offfwp p, .css-1offfwp span {
        color: var(--text-medium) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# DATABASE
# ============================================================================

def init_database():
    """Initialize database with minimal schema"""
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        created_by INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        uploaded_by INTEGER NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (uploaded_by) REFERENCES users(id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        pdf_id INTEGER,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (pdf_id) REFERENCES pdfs(id)
    )
    ''')
    
    # Create default superadmin
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'superadmin'")
    if cursor.fetchone()[0] == 0:
        password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ('superadmin', password_hash, 'superadmin')
        )
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_login(username, password):
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username = ? AND is_active = 1",
        (username,)
    )
    
    user = cursor.fetchone()
    conn.close()
    
    if user and user[2] == hash_password(password):
        return {
            'id': user[0],
            'username': user[1],
            'role': user[3]
        }
    return None

# ============================================================================
# AUTHENTICATION
# ============================================================================

def show_login_page():
    """Clean, light login page with proper contrast"""
    load_minimal_css()
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div style='height: 60px'></div>", unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div style='text-align: center; margin-bottom: 40px;'>
            <div style='font-size: 56px; color: #1e88e5; margin-bottom: 8px;'>📚</div>
            <h1 style='font-size: 36px; font-weight: 700; color: #1a237e; margin-bottom: 8px;'>
                Chat PDF
            </h1>
            <p style='color: #5c6bc0; font-size: 18px;'>
                AI Document Assistant
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login card
        with st.container():
            st.markdown("<div class='clean-card' style='max-width: 400px; margin: 0 auto;'>", unsafe_allow_html=True)
            
            st.markdown("<h3 style='color: #1a237e; margin-bottom: 24px;'>Sign In to Continue</h3>", unsafe_allow_html=True)
            
            # Login form
            username = st.text_input("Username", placeholder="Enter your username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_btn = st.button("Sign In", use_container_width=True, type="primary")
            
            with col_btn2:
                if st.button("Clear", use_container_width=True, type="secondary"):
                    st.rerun()
            
            if login_btn:
                if username and password:
                    user = verify_login(username, password)
                    if user:
                        st.session_state.update({
                            'logged_in': True,
                            'user_id': user['id'],
                            'username': user['username'],
                            'role': user['role']
                        })
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")
            
            # Demo credentials
            with st.expander("📋 Demo Account", expanded=False):
                st.markdown("""
                <div style='padding: 12px; background: #e3f2fd; border-radius: 8px;'>
                    <strong style='color: #1a237e;'>SuperAdmin Account</strong><br>
                    • Username: <code>superadmin</code><br>
                    • Password: <code>admin123</code>
                </div>
                <p style='color: #5c6bc0; font-size: 14px; margin-top: 12px;'>
                    Create admin and user accounts after login
                </p>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Features section
        st.markdown("<div style='height: 60px'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #1a237e; margin-bottom: 32px;'>Key Features</h3>", unsafe_allow_html=True)
        
        features = [
            ("🤖", "AI-Powered Q&A", "Ask questions and get instant answers from your PDFs"),
            ("📚", "Document Management", "Organize and manage all your PDF documents"),
            ("👥", "Multi-Role System", "Different access levels for different users"),
            ("💬", "Persistent Chat", "Save and revisit all your conversations")
        ]
        
        cols = st.columns(2)
        for idx, (icon, title, desc) in enumerate(features):
            with cols[idx % 2]:
                st.markdown(f"""
                <div style='margin-bottom: 24px; padding: 16px; background: white; border: 2px solid #bbdefb; border-radius: 12px;'>
                    <div style='font-size: 28px; color: #1e88e5; margin-bottom: 12px;'>{icon}</div>
                    <div style='font-weight: 600; color: #1a237e; margin-bottom: 8px;'>{title}</div>
                    <div style='font-size: 14px; color: #5c6bc0; line-height: 1.5;'>{desc}</div>
                </div>
                """, unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================

def render_sidebar():
    """Light sidebar with blue elements"""
    
    # Sidebar header
    st.sidebar.markdown("""
    <div class='sidebar-header'>
        <div style='font-size: 32px; color: #1e88e5; margin-bottom: 8px;'>📚</div>
        <h2 style='font-size: 20px; font-weight: 700;'>Chat PDF</h2>
        <p style='font-size: 14px;'>AI Document Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # User info
    role = st.session_state.get('role', 'user')
    username = st.session_state.get('username', 'User')
    
    role_colors = {
        'superadmin': {'bg': '#e8eaf6', 'text': '#3f51b5', 'label': 'SuperAdmin'},
        'admin': {'bg': '#e3f2fd', 'text': '#1976d2', 'label': 'Admin'},
        'user': {'bg': '#e0f2f1', 'text': '#00796b', 'label': 'User'}
    }
    
    role_color = role_colors.get(role, role_colors['user'])
    
    st.sidebar.markdown(f"""
    <div class='user-info-card'>
        <div class='username'>{username}</div>
        <div class='role-badge' style='background: {role_color['bg']}; color: {role_color['text']}; border-color: {role_color['text']}20;'>
            {role_color['label']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation
    st.sidebar.markdown("<div class='nav-section'>", unsafe_allow_html=True)
    st.sidebar.markdown("<div class='nav-section-title'>Main Navigation</div>", unsafe_allow_html=True)
    
    pages = [
        ("📊", "Dashboard", "Dashboard"),
        ("💬", "Chat", "User Chat"),
        ("📄", "Documents", "My Documents"),
    ]
    
    if role in ['admin', 'superadmin']:
        pages.append(("📤", "Upload", "Upload PDFs"))
    
    if role == 'superadmin':
        pages.extend([
            ("👥", "User Management", "User Management"),
            ("📈", "Analytics", "Analytics"),
            ("⚙️", "Settings", "System Settings")
        ])
    
    for icon, label, page_name in pages:
        is_active = st.session_state.get('selected_page') == page_name
        btn_type = "primary" if is_active else "secondary"
        
        if st.sidebar.button(
            f"{icon} {label}",
            key=f"nav_{page_name}",
            use_container_width=True,
            type=btn_type
        ):
            st.session_state.selected_page = page_name
            st.rerun()
    
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    # Logout button
    st.sidebar.markdown("<div style='padding: 0 16px; margin-top: 40px;'>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Logout", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
# ============================================================================
# DASHBOARD
# ============================================================================

def show_dashboard():
    """Light dashboard with blue accents"""
    load_minimal_css()
    
    # Welcome header
    st.markdown(f"""
    <div style='margin-bottom: 40px;'>
        <h1 style='font-size: 32px; font-weight: 700; color: #1a237e; margin-bottom: 8px;'>
            Welcome back, {st.session_state.get('username', 'User')}!
        </h1>
        <p style='color: #5c6bc0; font-size: 16px;'>
            Here's an overview of your documents and recent activity
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics
    st.markdown("<div class='section-header'>System Overview</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size: 24px; color: #1e88e5; margin-bottom: 12px;'>👥</div>
            <div class='metric-value'>156</div>
            <div class='metric-label'>Total Users</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size: 24px; color: #1e88e5; margin-bottom: 12px;'>📚</div>
            <div class='metric-value'>342</div>
            <div class='metric-label'>PDF Documents</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size: 24px; color: #1e88e5; margin-bottom: 12px;'>💬</div>
            <div class='metric-value'>1,234</div>
            <div class='metric-label'>Chat Sessions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size: 24px; color: #1e88e5; margin-bottom: 12px;'>💾</div>
            <div class='metric-value'>4.2 GB</div>
            <div class='metric-label'>Storage Used</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# OTHER PAGES
# ============================================================================

def show_user_chat():
    """Chat interface page"""
    st.title("💬 Chat")
    st.markdown("Chat with your PDF documents using AI")
    
    # Placeholder for chat interface
    with st.container():
        st.info("Chat interface will be implemented here")

def show_my_documents():
    """Documents page"""
    st.title("📄 Documents")
    st.markdown("Manage your uploaded PDF files")
    
    # Placeholder for document management
    with st.container():
        st.info("Document management interface will be implemented here")

def show_upload_pdfs():
    """Upload page"""
    st.title("📤 Upload PDFs")
    st.markdown("Upload new PDF documents to the system")
    
    with st.container():
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        if uploaded_file is not None:
            st.success(f"File '{uploaded_file.name}' uploaded successfully")
            # Add upload logic here

def show_user_management():
    """User management page"""
    st.title("👥 User Management")
    st.markdown("Manage user accounts and permissions")
    
    # Only superadmin can access
    if st.session_state.get('role') != 'superadmin':
        st.error("Access denied. Superadmin only.")
        return
    
    with st.container():
        # Add user form
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
            with col2:
                new_role = st.selectbox("Role", ["user", "admin"])
                new_email = st.text_input("Email (optional)")
            
            if st.form_submit_button("Add User", type="primary"):
                st.success(f"User '{new_username}' added successfully")
        
        # User list
        st.markdown("<div class='section-header'>User List</div>", unsafe_allow_html=True)
        
        users = [
            ("superadmin", "superadmin", "Active"),
            ("admin1", "admin", "Active"),
            ("user1", "user", "Active"),
            ("user2", "user", "Inactive")
        ]
        
        for username, role, status in users:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.text(username)
            with col2:
                st.text(role)
            with col3:
                st.text(status)
            with col4:
                if username != "superadmin":
                    st.button("Edit", key=f"edit_{username}")

def show_analytics():
    """Analytics page"""
    st.title("📈 Analytics")
    st.markdown("System usage statistics and reports")
    
    if st.session_state.get('role') not in ['superadmin', 'admin']:
        st.error("Access denied. Admin or Superadmin only.")
        return
    
    with st.container():
        st.info("Analytics dashboard will be implemented here")

def show_system_settings():
    """Settings page"""
    st.title("⚙️ Settings")
    st.markdown("System configuration and settings")
    
    if st.session_state.get('role') != 'superadmin':
        st.error("Access denied. Superadmin only.")
        return
    
    with st.container():
        st.info("System settings will be implemented here")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application"""
    
    # Initialize database
    init_database()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = 'Dashboard'
    
    # Check authentication
    if not st.session_state.logged_in:
        show_login_page()
        return
    
    # Load minimal CSS
    load_minimal_css()
    
    # Render sidebar
    render_sidebar()
    
    # Render selected page
    selected_page = st.session_state.get('selected_page', 'Dashboard')
    
    if selected_page == 'Dashboard':
        show_dashboard()
    elif selected_page == 'User Chat':
        show_user_chat()
    elif selected_page == 'My Documents':
        show_my_documents()
    elif selected_page == 'Upload PDFs':
        show_upload_pdfs()
    elif selected_page == 'User Management':
        show_user_management()
    elif selected_page == 'Analytics':
        show_analytics()
    elif selected_page == 'System Settings':
        show_system_settings()
    else:
        show_dashboard()

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()