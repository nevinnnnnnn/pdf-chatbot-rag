import streamlit as st
from core.auth import check_authentication, login_page, logout
from core.database import init_database

# Initialize database
init_database()

# Page config
st.set_page_config(
    page_title="DocChat AI - Login",
    page_icon="⚡",
    layout="wide"
)

# Load custom CSS
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None

# Check authentication
if not check_authentication():
    login_page()
else:
    # Show user info in sidebar
    user = st.session_state.user
    
    with st.sidebar:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 12px; margin-bottom: 20px;'>
                <div style='color: white; font-size: 14px; opacity: 0.9;'>Logged in as</div>
                <div style='color: white; font-size: 18px; font-weight: 600;'>{user['username']}</div>
                <div style='color: white; font-size: 12px; opacity: 0.8; text-transform: uppercase;'>{user['role']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    # Redirect based on role
    role = user["role"]
    
    st.markdown("""
        <div style='text-align: center; padding: 100px 20px;'>
            <h1 style='font-size: 48px; margin-bottom: 20px;'>⚡ Welcome to DocChat AI</h1>
            <p style='font-size: 18px; color: #888;'>Select a page from the sidebar to get started</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.info(f"""
        **Your Role:** {role.upper()}
        
        **Available Pages:**
        - {"👤 User Chat - Ask questions about PDFs" if role in ["user", "admin", "superadmin"] else ""}
        - {"👨‍💼 Admin Panel - Upload PDFs and manage users" if role in ["admin", "superadmin"] else ""}
        - {"👑 Super Admin - Full system control" if role == "superadmin" else ""}
    """)