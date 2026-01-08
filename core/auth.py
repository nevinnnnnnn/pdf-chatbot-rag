import streamlit as st
from core.database import authenticate_user, init_database

def check_authentication():
    """Check if user is authenticated"""
    return "user" in st.session_state and st.session_state.user is not None

def require_auth(required_role: str = None):
    """Decorator to require authentication"""
    if not check_authentication():
        st.error("🔒 Please login to access this page")
        st.stop()
    
    if required_role:
        user_role = st.session_state.user["role"]
        
        # Role hierarchy: superadmin > admin > user
        role_levels = {"user": 1, "admin": 2, "superadmin": 3}
        
        if role_levels.get(user_role, 0) < role_levels.get(required_role, 999):
            st.error(f"🚫 Access denied. Required role: {required_role}")
            st.stop()

def login_page():
    """Display login page"""
    st.markdown("""
        <div style='text-align: center; padding: 60px 20px;'>
            <h1 style='font-size: 48px; margin-bottom: 12px;'>⚡ DocChat AI</h1>
            <p style='color: #888; font-size: 18px;'>Multi-User PDF Analysis System</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.subheader("🔐 Login")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.success(f"✅ Welcome, {user['username']}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                else:
                    st.warning("⚠️ Please enter both username and password")
        
        st.info("""
            **Default Accounts:**
            - Super Admin: `superadmin` / `superadmin123`
            
            Contact your administrator for credentials.
        """)

def logout():
    """Logout user"""
    if "user" in st.session_state:
        del st.session_state.user
    st.rerun()