import streamlit as st
import sqlite3
from datetime import datetime

def get_user_stats(user_id):
    """Get user statistics from database"""
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Get user's PDF count
    cursor.execute('SELECT COUNT(*) FROM pdfs WHERE uploaded_by = ?', (user_id,))
    pdf_count = cursor.fetchone()[0]
    
    # Get user's chat count
    cursor.execute('SELECT COUNT(*) FROM chat_history WHERE user_id = ?', (user_id,))
    chat_count = cursor.fetchone()[0]
    
    conn.close()
    return pdf_count, chat_count

def get_system_stats():
    """Get system-wide statistics for superadmin"""
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Get total users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # Get total PDFs
    cursor.execute('SELECT COUNT(*) FROM pdfs')
    total_pdfs = cursor.fetchone()[0]
    
    # Get total chats
    cursor.execute('SELECT COUNT(*) FROM chat_history')
    total_chats = cursor.fetchone()[0]
    
    # Get active users today
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM chat_history WHERE DATE(timestamp) = ?', (today,))
    active_today = cursor.fetchone()[0]
    
    conn.close()
    return total_users, total_pdfs, total_chats, active_today

def render_sidebar():
    """Render the sidebar navigation"""
    
    # Get user info from session
    user_role = st.session_state.get('role', 'user')
    username = st.session_state.get('username', 'User')
    user_id = st.session_state.get('user_id', 0)
    
    # Sidebar header with logo
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 24px 16px; border-bottom: 1px solid #e2e8f0;">
        <div style="font-size: 48px; margin-bottom: 8px; color: #2563eb;">📚</div>
        <h1 style="font-size: 24px; font-weight: 800; color: #1e293b; margin: 0;">Chat PDF</h1>
        <p style="font-size: 14px; color: #64748b; margin: 4px 0 0 0;">AI Document Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # User info section
    st.sidebar.markdown("""
    <div style="padding: 20px 16px; border-bottom: 1px solid #e2e8f0;">
        <div style="display: flex; align-items: center; margin-bottom: 16px;">
            <div style="
                background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
                width: 48px; 
                height: 48px; 
                border-radius: 50%; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                margin-right: 12px;
                font-size: 20px;
                color: white;
            ">
                """ + ("👑" if user_role == "superadmin" else "👤" if user_role == "admin" else "🙂") + """
            </div>
            <div>
                <div style="font-weight: 700; color: #1e293b; font-size: 16px;">""" + username + """</div>
                <div style="
                    display: inline-block;
                    background: """ + ("linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)" if user_role == "superadmin" else 
                                    "linear-gradient(135deg, #0891b2 0%, #0e7490 100%)" if user_role == "admin" else 
                                    "linear-gradient(135deg, #10b981 0%, #059669 100%)") + """;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 11px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-top: 4px;
                ">
                    """ + user_role.upper() + """
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation sections
    st.sidebar.markdown("""
    <div style="padding: 8px 0;">
        <div style="
            color: #64748b;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 12px 20px 8px 20px;
        ">
            📱 Main Navigation
        </div>
    """, unsafe_allow_html=True)
    
    # Navigation options
    nav_options = [
        {"icon": "🏠", "label": "Dashboard", "page": "Dashboard", "roles": ["superadmin", "admin", "user"]},
        {"icon": "💬", "label": "User Chat", "page": "User Chat", "roles": ["superadmin", "admin", "user"]},
        {"icon": "📄", "label": "My Documents", "page": "My Documents", "roles": ["superadmin", "admin", "user"]},
    ]
    
    # Add Upload PDFs for admins and superadmins
    if user_role in ["superadmin", "admin"]:
        nav_options.append({"icon": "📤", "label": "Upload PDFs", "page": "Upload PDFs", "roles": ["superadmin", "admin"]})
    
    # Render navigation buttons
    for option in nav_options:
        if user_role in option["roles"]:
            is_active = st.session_state.get('selected_page', 'Dashboard') == option["page"]
            button_style = f"""
            background: {'#eff6ff' if is_active else 'transparent'};
            color: {'#2563eb' if is_active else '#475569'};
            border-left: {'4px solid #2563eb' if is_active else '4px solid transparent'};
            """
            
            if st.sidebar.button(
                f"{option['icon']} {option['label']}",
                key=f"nav_{option['page']}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.selected_page = option["page"]
                st.rerun()
    
    # SuperAdmin Panel Section
    if user_role == "superadmin":
        st.sidebar.markdown("""
        <div style="
            color: #64748b;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 24px 20px 8px 20px;
            border-top: 1px solid #e2e8f0;
            margin-top: 8px;
        ">
            👑 Administration
        </div>
        """, unsafe_allow_html=True)
        
        admin_options = [
            {"icon": "👥", "label": "User Management", "page": "User Management"},
            {"icon": "📑", "label": "Document Library", "page": "Document Library"},
            {"icon": "📊", "label": "Analytics", "page": "Analytics"},
            {"icon": "⚙️", "label": "System Settings", "page": "System Settings"},
        ]
        
        for option in admin_options:
            is_active = st.session_state.get('selected_page', 'Dashboard') == option["page"]
            
            if st.sidebar.button(
                f"{option['icon']} {option['label']}",
                key=f"admin_{option['page']}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.selected_page = option["page"]
                st.rerun()
    
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    # Quick Stats for SuperAdmin
    if user_role == "superadmin":
        st.sidebar.markdown("""
        <div style="
            border-top: 1px solid #e2e8f0;
            margin-top: 16px;
            padding: 20px 16px;
        ">
            <div style="
                color: #64748b;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 16px;
            ">
                📈 Quick Stats
            </div>
        """, unsafe_allow_html=True)
        
        try:
            total_users, total_pdfs, total_chats, active_today = get_system_stats()
            
            col1, col2 = st.sidebar.columns(2)
            with col1:
                st.metric("Users", total_users)
                st.metric("PDFs", total_pdfs)
            with col2:
                st.metric("Chats", total_chats)
                st.metric("Active", active_today)
        except:
            # Fallback if database not ready
            col1, col2 = st.sidebar.columns(2)
            with col1:
                st.metric("Users", "0")
                st.metric("PDFs", "0")
            with col2:
                st.metric("Chats", "0")
                st.metric("Active", "0")
        
        st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    # Personal Stats for all users
    else:
        try:
            pdf_count, chat_count = get_user_stats(user_id)
            
            st.sidebar.markdown(f"""
            <div style="
                border-top: 1px solid #e2e8f0;
                margin-top: 16px;
                padding: 20px 16px;
            ">
                <div style="
                    color: #64748b;
                    font-size: 12px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 16px;
                ">
                    📊 Your Stats
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.sidebar.columns(2)
            with col1:
                st.metric("Your PDFs", pdf_count)
            with col2:
                st.metric("Your Chats", chat_count)
            
            st.sidebar.markdown("</div>", unsafe_allow_html=True)
        except:
            pass
    
    # Logout section
    st.sidebar.markdown("""
    <div style="
        border-top: 1px solid #e2e8f0;
        margin-top: 16px;
        padding: 20px 16px;
    ">
    """, unsafe_allow_html=True)
    
    if st.sidebar.button(
        "🚪 Logout", 
        use_container_width=True,
        type="secondary"
    ):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.sidebar.markdown("""
    </div>
    
    <div style="
        padding: 16px;
        text-align: center;
        color: #94a3b8;
        font-size: 12px;
        border-top: 1px solid #e2e8f0;
    ">
        <p style="margin: 0;">Chat PDF v1.0</p>
        <p style="margin: 4px 0 0 0;">© 2024 All rights reserved</p>
    </div>
    """, unsafe_allow_html=True)

# For testing the sidebar independently
if __name__ == "__main__":
    # Test the sidebar with sample session data
    st.set_page_config(
        page_title="Sidebar Test",
        page_icon="📚",
        layout="wide",
    )
    
    # Set test session state
    if 'role' not in st.session_state:
        st.session_state.role = "superadmin"
    if 'username' not in st.session_state:
        st.session_state.username = "Test User"
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = "Dashboard"
    
    render_sidebar()
    st.write("Main content area")