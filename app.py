import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import json
import warnings
import re

# Suppress CryptographyDeprecationWarning about ARC4
warnings.filterwarnings("ignore", message="ARC4 has been moved to")

# Page configuration
st.set_page_config(
    page_title="Chat PDF - Document AI Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load your custom CSS
def load_custom_css():
    with open('style.css', 'r') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Additional CSS for login page
def load_login_css():
    st.markdown("""
    <style>
    /* Login page specific styling */
    .login-page-container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 20px;
    }
    
    .login-card {
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        width: 100%;
        max-width: 440px;
        padding: 40px;
        border: 1px solid #e2e8f0;
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 40px;
    }
    
    .login-logo {
        font-size: 64px;
        margin-bottom: 16px;
        color: #2563eb;
    }
    
    .login-title {
        font-size: 32px;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 8px;
    }
    
    .login-subtitle {
        font-size: 16px;
        color: #64748b;
        font-weight: 500;
    }
    
    .login-input {
        margin-bottom: 24px;
    }
    
    .login-input label {
        display: block;
        color: #475569;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .login-button-container {
        margin-top: 32px;
    }
    
    .login-button {
        width: 100%;
        padding: 14px;
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .login-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.3);
    }
    
    .login-button:active {
        transform: translateY(0);
    }
    
    .login-footer {
        text-align: center;
        margin-top: 32px;
        padding-top: 24px;
        border-top: 1px solid #e2e8f0;
        color: #64748b;
        font-size: 14px;
    }
    
    .demo-credentials {
        background: #eff6ff;
        border: 1px solid #dbeafe;
        border-radius: 12px;
        padding: 20px;
        margin-top: 24px;
    }
    
    .demo-credentials h4 {
        color: #1e40af;
        margin-bottom: 12px;
        font-size: 16px;
    }
    
    .demo-credentials code {
        background: #dbeafe;
        padding: 4px 8px;
        border-radius: 6px;
        font-family: 'Courier New', monospace;
        color: #1e40af;
    }
    
    .feature-showcase {
        max-width: 1000px;
        margin: 60px auto;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 24px;
        margin-top: 40px;
    }
    
    .feature-item {
        background: white;
        border-radius: 16px;
        padding: 32px;
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .feature-item:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
        border-color: #93c5fd;
    }
    
    .feature-icon {
        font-size: 40px;
        margin-bottom: 20px;
        color: #2563eb;
    }
    
    .feature-title {
        font-size: 20px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 12px;
    }
    
    .feature-desc {
        color: #64748b;
        line-height: 1.6;
    }
    
    /* Role badges for main app */
    .role-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-left: 12px;
    }
    
    .superadmin-badge {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white;
    }
    
    .admin-badge {
        background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
        color: white;
    }
    
    .user-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    
    /* Main app header */
    .main-header {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 32px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Database functions (same as before)
def init_database():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        role TEXT NOT NULL,
        created_by INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
    ''')
    
    # PDFs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        uploaded_by INTEGER NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        file_size INTEGER,
        description TEXT,
        is_public INTEGER DEFAULT 0,
        FOREIGN KEY (uploaded_by) REFERENCES users(id)
    )
    ''')
    
    # Chat history table
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
    
    # Permissions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        pdf_id INTEGER NOT NULL,
        permission_type TEXT DEFAULT 'read',
        granted_by INTEGER,
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (pdf_id) REFERENCES pdfs(id),
        FOREIGN KEY (granted_by) REFERENCES users(id)
    )
    ''')
    
    # Analytics table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        pdf_id INTEGER,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (pdf_id) REFERENCES pdfs(id)
    )
    ''')
    
    # Create default superadmin if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'superadmin'")
    if not cursor.fetchone():
        # Default password: admin123
        password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('''
        INSERT INTO users (username, password_hash, role, email)
        VALUES (?, ?, ?, ?)
        ''', ('superadmin', password_hash, 'superadmin', 'superadmin@example.com'))
    
    conn.commit()
    return conn

# Authentication functions (same as before)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    return hash_password(password) == password_hash

def login_user(username, password):
    conn = init_database()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, username, password_hash, role FROM users 
    WHERE username = ? AND is_active = 1
    ''', (username,))
    
    user = cursor.fetchone()
    
    if user and verify_password(password, user[2]):
        # Update last login
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                      (datetime.now(), user[0]))
        conn.commit()
        conn.close()
        
        return {
            'id': user[0],
            'username': user[1],
            'role': user[3]
        }
    
    conn.close()
    return None

def logout_user():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# Updated Login Page with Light Theme
def show_login_page():
    load_custom_css()  # Load your style.css
    load_login_css()   # Load login-specific CSS
    
    # Main login container
    st.markdown('<div class="login-page-container">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-card">
            <div class="login-header">
                <div class="login-logo">📚</div>
                <h1 class="login-title">Chat PDF</h1>
                <p class="login-subtitle">AI-Powered Document Assistant</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Login form
        st.markdown('<div class="login-input">', unsafe_allow_html=True)
        username = st.text_input("👤 Username", placeholder="Enter your username")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="login-input">', unsafe_allow_html=True)
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Login button
        st.markdown('<div class="login-button-container">', unsafe_allow_html=True)
        if st.button("🚪 Sign In", use_container_width=True, type="primary"):
            if username and password:
                user = login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user['id']
                    st.session_state.username = user['username']
                    st.session_state.role = user['role']
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
            else:
                st.warning("⚠️ Please enter both username and password")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Demo credentials
        with st.expander("📋 Demo Credentials", expanded=True):
            st.markdown("""
            <div class="demo-credentials">
                <h4>SuperAdmin Account</h4>
                <p><strong>Username:</strong> <code>superadmin</code></p>
                <p><strong>Password:</strong> <code>admin123</code></p>
                <p style="margin-top: 12px; font-size: 13px; color: #64748b;">
                    After login, you can create admin and user accounts from the dashboard.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="login-footer">
            <p>© 2024 Chat PDF. All rights reserved.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close login-card
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close login-page-container
    
    # Features showcase
    st.markdown("""
    <div class="feature-showcase">
        <h2 style="text-align: center; color: #1e293b; margin-bottom: 16px;">✨ Powerful Features</h2>
        <p style="text-align: center; color: #64748b; max-width: 600px; margin: 0 auto 40px;">
            Everything you need to manage, analyze, and interact with your PDF documents
        </p>
    """, unsafe_allow_html=True)
    
    # Feature grid
    features = [
        {
            "icon": "📚",
            "title": "Smart Document Management",
            "desc": "Upload, organize, and categorize PDFs with intelligent tagging and search capabilities."
        },
        {
            "icon": "🤖",
            "title": "AI-Powered Q&A",
            "desc": "Ask questions about your documents and get instant, accurate answers from advanced AI."
        },
        {
            "icon": "👑",
            "title": "Role-Based Access Control",
            "desc": "SuperAdmin, Admin, and User roles with granular permissions and access controls."
        },
        {
            "icon": "📊",
            "title": "Advanced Analytics",
            "desc": "Track usage, monitor performance, and gain insights from comprehensive analytics."
        },
        {
            "icon": "💬",
            "title": "Persistent Chat History",
            "desc": "Your conversations are saved and easily searchable across all login sessions."
        },
        {
            "icon": "🔒",
            "title": "Enterprise Security",
            "desc": "Bank-level security with encrypted storage and secure authentication protocols."
        }
    ]
    
    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    for feature in features:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1 if features.index(feature) % 3 == 0 else col2 if features.index(feature) % 3 == 1 else col3:
            st.markdown(f"""
            <div class="feature-item">
                <div class="feature-icon">{feature['icon']}</div>
                <h3 class="feature-title">{feature['title']}</h3>
                <p class="feature-desc">{feature['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close feature-showcase

# Main app function
def main():
    # Check if user is logged in
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        show_login_page()
    else:
        # Import sidebar function from sidebar module
        from sidebar import render_sidebar
        
        # Load main app CSS
        load_custom_css()
        
        # Render sidebar
        render_sidebar()
        
        # Main content area
        st.markdown(f"""
        <div class="main-header">
            <h1 style="font-size: 32px; margin-bottom: 8px;">Welcome back, {st.session_state.username}!</h1>
            <p style="font-size: 16px; color: #64748b; margin-bottom: 16px;">
                You are logged in as: 
                <span class="role-badge {st.session_state.role}-badge">
                    {st.session_state.role.upper()}
                </span>
            </p>
            <p style="font-size: 14px; color: #94a3b8;">
                Last login: Today at {datetime.now().strftime("%I:%M %p")}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Get selected page from session state
        selected_page = st.session_state.get('selected_page', 'Dashboard')
        
        # Page routing
        if selected_page == "Dashboard":
            show_dashboard()
        elif selected_page == "User Chat":
            show_user_chat()
        elif selected_page == "My Documents":
            show_my_documents()
        elif selected_page == "Upload PDFs":
            show_upload_pdfs()
        elif selected_page == "User Management":
            show_user_management()
        elif selected_page == "Document Library":
            show_document_library()
        elif selected_page == "Analytics":
            show_analytics()
        elif selected_page == "System Settings":
            show_system_settings()
        else:
            show_dashboard()

# Page functions (to be implemented separately)
def show_dashboard():
    st.title("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", "156", "+12 this month")
    
    with col2:
        st.metric("Total PDFs", "342", "+8 this week")
    
    with col3:
        st.metric("Chat Sessions", "1,234", "+45 today")
    
    with col4:
        st.metric("Storage Used", "4.2 GB", "80%")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Recent Activity")
        st.write("Activity chart will be displayed here")
        
        # Recent chat history
        st.subheader("💬 Recent Chats")
        st.write("Recent chat conversations will appear here")
    
    with col2:
        st.subheader("🚀 Quick Actions")
        
        if st.button("💬 Start New Chat", use_container_width=True):
            st.session_state.selected_page = "User Chat"
            st.rerun()
        
        if st.button("📤 Upload PDF", use_container_width=True):
            st.session_state.selected_page = "Upload PDFs"
            st.rerun()
        
        if st.session_state.role == "superadmin":
            if st.button("👥 Manage Users", use_container_width=True):
                st.session_state.selected_page = "User Management"
                st.rerun()
            
            if st.button("📊 View Analytics", use_container_width=True):
                st.session_state.selected_page = "Analytics"
                st.rerun()

def show_user_chat():
    st.title("💬 User Chat")
    st.info("Chat interface will be implemented in the next file")
    
    # Placeholder for chat interface
    st.write("This is where users can chat with their PDF documents.")
    st.write("Features to be implemented:")
    st.write("- PDF selection")
    st.write("- AI-powered Q&A")
    st.write("- Chat history")
    st.write("- File upload for chat")

def show_my_documents():
    st.title("📄 My Documents")
    st.write("Your uploaded documents will appear here.")

def show_upload_pdfs():
    st.title("📤 Upload PDFs")
    st.write("PDF upload interface will be implemented here.")

def show_user_management():
    st.title("👥 User Management")
    st.write("User management interface for superadmin.")

def show_document_library():
    st.title("📑 Document Library")
    st.write("Complete document library for superadmin.")

def show_analytics():
    st.title("📈 Analytics")
    st.write("System analytics and reports.")

def show_system_settings():
    st.title("⚙️ System Settings")
    st.write("System configuration and settings.")

if __name__ == "__main__":
    main()