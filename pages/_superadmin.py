import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
import time

# Add path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.auth import require_auth, check_authentication
    from core.database import (
        get_all_users, get_all_pdfs, get_chat_history,
        create_user, delete_user, update_user, delete_pdf
    )
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# ------------------------------------
# Page Configuration
# ------------------------------------
st.set_page_config(
    page_title="DocChat AI - Super Admin",
    page_icon="👑",
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
        background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
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
        background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%);
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
        margin-bottom: 10px;
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
    .plotly-container {
        background: rgba(0,0,0,0);
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------
# Helper Functions
# ------------------------------------
def get_system_stats():
    """Get system statistics (fallback if not in database module)"""
    try:
        users = get_all_users()
        pdfs = get_all_pdfs()
        chats = get_chat_history(limit=1000)  # Get more for stats
        
        # Count users by role
        user_counts = {"superadmin": 0, "admin": 0, "user": 0}
        for user in users:
            role = user.get('role', 'user')
            if role in user_counts:
                user_counts[role] += 1
        
        stats = {
            'users': user_counts,
            'total_pdfs': len(pdfs),
            'total_chats': len(chats),
            'active_users': len(set([c.get('user_id', '') for c in chats if c.get('user_id')])),
            'active_pdfs': len(set([c.get('pdf_id', '') for c in chats if c.get('pdf_id')]))
        }
        return stats
    except Exception as e:
        st.warning(f"Could not get system stats: {e}")
        return {
            'users': {'superadmin': 0, 'admin': 0, 'user': 0},
            'total_pdfs': 0,
            'total_chats': 0,
            'active_users': 0,
            'active_pdfs': 0
        }

def require_auth_wrapper(required_role="superadmin"):
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

# ------------------------------------
# Authentication Check
# ------------------------------------
user = require_auth_wrapper("superadmin")

# Sidebar
with st.sidebar:
    st.markdown(f"""
        <div class='user-info-card'>
            <div class='user-info-label'>Super Admin Panel</div>
            <div class='user-info-name'>{user['username']}</div>
            <div class='user-info-role'>👑 {user['role']}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Home button
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")
    
    st.divider()
    
    # Quick stats
    try:
        stats = get_system_stats()
        st.markdown("### 📊 Quick Stats")
        st.metric("Total Users", sum(stats['users'].values()))
        st.metric("Total PDFs", stats['total_pdfs'])
        st.metric("Total Queries", stats['total_chats'])
    except:
        pass

# Page Header
st.markdown("""
    <div class='page-header'>
        <div class='page-title'>👑 Super Admin Dashboard</div>
        <div class='page-subtitle'>Complete system control and monitoring</div>
    </div>
""", unsafe_allow_html=True)

# Get system stats
stats = get_system_stats()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    "👥 All Users", 
    "👨‍💼 Admins", 
    "📚 All PDFs", 
    "📈 Analytics"
])

# ==================== TAB 1: OVERVIEW ====================
with tab1:
    st.markdown("### 📊 System Overview")
    
    # Key Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-value'>{stats['users'].get('superadmin', 0)}</div>
                <div class='stat-label'>Super Admins</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-value'>{stats['users'].get('admin', 0)}</div>
                <div class='stat-label'>Admins</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-value'>{stats['users'].get('user', 0)}</div>
                <div class='stat-label'>Users</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-value'>{stats['total_pdfs']}</div>
                <div class='stat-label'>Total PDFs</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-value'>{stats['total_chats']}</div>
                <div class='stat-label'>Total Queries</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👥 Users by Role")
        
        role_data = pd.DataFrame([
            {"Role": role.capitalize(), "Count": count}
            for role, count in stats['users'].items() if count > 0
        ])
        
        if not role_data.empty:
            fig = px.pie(
                role_data,
                values='Count',
                names='Role',
                color_discrete_sequence=['#7c3aed', '#2563eb', '#0891b2']
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No user data available")
    
    with col2:
        st.markdown("#### 📊 Activity (Last 7 Days)")
        
        try:
            chats = get_chat_history(limit=1000)
            if chats and len(chats) > 0:
                df = pd.DataFrame(chats)
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['date'] = df['timestamp'].dt.date
                    
                    # Last 7 days
                    last_7_days = [(datetime.now().date() - timedelta(days=i)) for i in range(6, -1, -1)]
                    activity_series = df[df['date'].isin(last_7_days)].groupby('date').size()
                    activity = pd.Series([0] * 7, index=last_7_days)
                    activity.update(activity_series)
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            x=[d.strftime('%m/%d') for d in activity.index],
                            y=activity.values,
                            marker_color='#2563eb'
                        )
                    ])
                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Queries",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No timestamp data available")
            else:
                st.info("No activity data available yet")
        except Exception as e:
            st.info(f"No activity data: {str(e)[:50]}...")
    
    st.markdown("---")
    st.markdown("#### 📜 Recent System Activity")
    
    try:
        chats = get_chat_history(limit=10)
        if chats and len(chats) > 0:
            df = pd.DataFrame(chats)
            # Ensure columns exist
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            if 'question' in df.columns:
                df['question'] = df['question'].astype(str).str[:80] + '...'
            
            # Select available columns
            available_cols = []
            for col in ['username', 'pdf_name', 'question', 'timestamp']:
                if col in df.columns:
                    available_cols.append(col)
            
            if available_cols:
                st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No data columns available")
        else:
            st.info("No activity yet")
    except Exception as e:
        st.info(f"Could not load recent activity: {str(e)[:50]}...")

# ==================== TAB 2: ALL USERS ====================
with tab2:
    st.markdown("### 👥 All Users")
    
    try:
        users = get_all_users()
    except Exception as e:
        st.error(f"Error loading users: {e}")
        users = []
    
    if users and len(users) > 0:
        # Prepare user data with safe defaults
        user_data = []
        for u in users:
            user_data.append({
                'id': u.get('id', ''),
                'username': u.get('username', 'Unknown'),
                'email': u.get('email', 'Unknown'),
                'role': u.get('role', 'user'),
                'is_active': '✅' if u.get('is_active', 0) == 1 else '❌',
                'created_at': pd.to_datetime(u.get('created_at', '1900-01-01')).strftime('%Y-%m-%d') if u.get('created_at') else 'Unknown',
                'last_login': pd.to_datetime(u.get('last_login', '1900-01-01')).strftime('%Y-%m-%d %H:%M') if u.get('last_login') else 'Never'
            })
        
        df = pd.DataFrame(user_data)
        
        st.dataframe(
            df[['id', 'username', 'email', 'role', 'is_active', 'created_at', 'last_login']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "username": st.column_config.TextColumn("Username", width="medium"),
                "email": st.column_config.TextColumn("Email", width="large"),
                "role": st.column_config.TextColumn("Role", width="small"),
                "is_active": st.column_config.TextColumn("Active", width="small"),
                "created_at": st.column_config.TextColumn("Created", width="medium"),
                "last_login": st.column_config.TextColumn("Last Login", width="medium")
            }
        )
        
        st.markdown("---")
        st.markdown("#### 🔧 User Management")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            user_options = [u.get('username', 'Unknown') for u in users]
            if user_options:
                user_to_modify = st.selectbox("Select User", user_options, key="user_select")
            else:
                st.info("No users available")
                user_to_modify = None
        
        with col2:
            action = st.selectbox("Action", ["Activate", "Deactivate", "Delete"], key="user_action")
        
        with col3:
            st.write("")
            st.write("")
            if user_to_modify and st.button("Execute Action", type="primary", use_container_width=True, key="execute_user_action"):
                selected = next((u for u in users if u.get('username') == user_to_modify), None)
                
                if selected:
                    try:
                        if action == "Activate":
                            update_user(selected['id'], is_active=True)
                            st.success(f"✅ Activated: {user_to_modify}")
                            time.sleep(1)
                            st.rerun()
                        elif action == "Deactivate":
                            update_user(selected['id'], is_active=False)
                            st.success(f"✅ Deactivated: {user_to_modify}")
                            time.sleep(1)
                            st.rerun()
                        elif action == "Delete":
                            if selected.get('role') == 'superadmin':
                                st.error("❌ Cannot delete superadmin users")
                            else:
                                delete_user(selected['id'])
                                st.success(f"✅ Deleted: {user_to_modify}")
                                time.sleep(1)
                                st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("User not found")
    else:
        st.info("No users found")

# ==================== TAB 3: ADMINS ====================
with tab3:
    st.markdown("### 👨‍💼 Admin Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### ➕ Create New Admin")
        
        with st.form("create_admin", clear_on_submit=True):
            admin_username = st.text_input("Username", placeholder="admin_user")
            admin_email = st.text_input("Email", placeholder="admin@example.com")
            admin_password = st.text_input("Password", type="password", placeholder="********")
            admin_role = st.selectbox("Role", ["admin", "superadmin"])
            
            submit = st.form_submit_button("Create Admin", type="primary", use_container_width=True)
            
            if submit:
                if admin_username and admin_email and admin_password:
                    if len(admin_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        try:
                            success = create_user(
                                username=admin_username,
                                email=admin_email,
                                password=admin_password,
                                role=admin_role,
                                created_by=user['id']
                            )
                            
                            if success:
                                st.success(f"✅ Admin '{admin_username}' created!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Username or email already exists")
                        except Exception as e:
                            st.error(f"❌ Error creating user: {e}")
                else:
                    st.warning("⚠️ Please fill all fields")
    
    with col2:
        st.markdown("#### 📋 Admin List")
        
        try:
            all_users = get_all_users()
            admins = [u for u in all_users if u.get('role') in ['admin', 'superadmin']]
        except Exception as e:
            st.error(f"Error loading admins: {e}")
            admins = []
        
        if admins and len(admins) > 0:
            admin_data = []
            for a in admins:
                admin_data.append({
                    'username': a.get('username', 'Unknown'),
                    'email': a.get('email', 'Unknown'),
                    'role': a.get('role', 'admin'),
                    'is_active': '✅' if a.get('is_active', 0) == 1 else '❌',
                    'last_login': pd.to_datetime(a.get('last_login', '1900-01-01')).strftime('%Y-%m-%d %H:%M') if a.get('last_login') else 'Never'
                })
            
            df = pd.DataFrame(admin_data)
            
            st.dataframe(
                df[['username', 'email', 'role', 'is_active', 'last_login']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "username": st.column_config.TextColumn("Username", width="medium"),
                    "email": st.column_config.TextColumn("Email", width="large"),
                    "role": st.column_config.TextColumn("Role", width="small"),
                    "is_active": st.column_config.TextColumn("Active", width="small"),
                    "last_login": st.column_config.TextColumn("Last Login", width="medium")
                }
            )
        else:
            st.info("No admins found")

# ==================== TAB 4: ALL PDFs ====================
with tab4:
    st.markdown("### 📚 All PDFs")
    
    try:
        pdfs = get_all_pdfs()
    except Exception as e:
        st.error(f"Error loading PDFs: {e}")
        pdfs = []
    
    if pdfs and len(pdfs) > 0:
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total PDFs", len(pdfs))
        with col2:
            total_pages = sum(p.get('num_pages', 0) for p in pdfs)
            st.metric("Total Pages", total_pages)
        with col3:
            total_chunks = sum(p.get('num_chunks', 0) for p in pdfs)
            st.metric("Total Chunks", total_chunks)
        with col4:
            total_images = sum(p.get('num_images', 0) for p in pdfs)
            st.metric("Total Images", total_images)
        
        st.markdown("---")
        
        # PDF List
        pdf_data = []
        for p in pdfs:
            pdf_data.append({
                'id': p.get('id', ''),
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
            df[['id', 'original_name', 'uploader_name', 'num_pages', 'num_chunks', 'num_images', 'file_size', 'upload_date']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
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
            pdf_options = [f"{p.get('id', '')} - {p.get('original_name', 'Unknown')}" for p in pdfs]
            if pdf_options:
                pdf_to_delete = st.selectbox("Select PDF", pdf_options, key="delete_pdf")
            else:
                st.info("No PDFs available")
                pdf_to_delete = None
        
        with col2:
            st.write("")
            st.write("")
            if pdf_to_delete and st.button("Delete PDF", type="primary", use_container_width=True, key="confirm_delete_pdf"):
                try:
                    pdf_id = int(pdf_to_delete.split(" - ")[0])
                    delete_pdf(pdf_id)
                    st.success(f"✅ PDF deleted successfully!")
                    time.sleep(1)
                    st.rerun()
                except ValueError:
                    st.error("❌ Invalid PDF ID")
                except Exception as e:
                    st.error(f"❌ Error deleting PDF: {e}")
    else:
        st.info("📭 No PDFs in the system yet")

# ==================== TAB 5: ANALYTICS ====================
with tab5:
    st.markdown("### 📈 Advanced Analytics")
    
    try:
        chats = get_chat_history(limit=1000)
    except Exception as e:
        st.error(f"Error loading chat history: {e}")
        chats = []
    
    if chats and len(chats) > 0:
        try:
            df = pd.DataFrame(chats)
            
            # Ensure required columns exist
            if 'timestamp' not in df.columns:
                st.error("No timestamp data available")
                st.stop()
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            df['hour'] = df['timestamp'].dt.hour
            
            # Row 1: Activity over time
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📅 Daily Activity (Last 30 Days)")
                
                last_30_days = [(datetime.now().date() - timedelta(days=i)) for i in range(29, -1, -1)]
                daily_counts = df[df['date'].isin(last_30_days)].groupby('date').size()
                
                # Create full series for last 30 days
                daily_activity = pd.Series([0] * 30, index=last_30_days)
                daily_activity.update(daily_counts)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=[d.strftime('%m/%d') for d in daily_activity.index],
                    y=daily_activity.values,
                    mode='lines+markers',
                    line=dict(color='#2563eb', width=3),
                    marker=dict(size=8),
                    fill='tozeroy',
                    fillcolor='rgba(37, 99, 235, 0.2)'
                ))
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Number of Queries",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400,
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### ⏰ Hourly Activity Pattern")
                
                hourly_counts = df.groupby('hour').size()
                
                # Ensure all hours 0-23
                hourly_activity = pd.Series([0] * 24, index=range(24))
                hourly_activity.update(hourly_counts)
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=hourly_activity.index,
                    y=hourly_activity.values,
                    marker_color='#0891b2'
                ))
                fig.update_layout(
                    xaxis_title="Hour of Day",
                    yaxis_title="Number of Queries",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400,
                    xaxis=dict(tickmode='linear', tick0=0, dtick=2)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Row 2: User and PDF analytics
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 👥 Most Active Users")
                
                if 'username' in df.columns:
                    user_counts = df.groupby('username').size().sort_values(ascending=False).head(10)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=user_counts.values,
                        y=user_counts.index,
                        orientation='h',
                        marker_color='#7c3aed'
                    ))
                    fig.update_layout(
                        xaxis_title="Number of Queries",
                        yaxis_title="Username",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No username data available")
            
            with col2:
                st.markdown("#### 📚 Most Queried PDFs")
                
                if 'pdf_name' in df.columns:
                    pdf_counts = df[df['pdf_name'].notna()].groupby('pdf_name').size().sort_values(ascending=False).head(10)
                    
                    if len(pdf_counts) > 0:
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=pdf_counts.values,
                            y=pdf_counts.index,
                            orientation='h',
                            marker_color='#10b981'
                        ))
                        fig.update_layout(
                            xaxis_title="Number of Queries",
                            yaxis_title="PDF Name",
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No PDF query data available")
                else:
                    st.info("No PDF name data available")
            
            st.markdown("---")
            
            # Row 3: Detailed activity log
            st.markdown("#### 📜 Detailed Activity Log")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                user_options = ["All"] + list(df['username'].unique()) if 'username' in df.columns else ["All"]
                filter_user = st.selectbox("Filter by User", user_options)
            
            with col2:
                pdf_options = ["All"]
                if 'pdf_name' in df.columns:
                    pdf_options += list(df[df['pdf_name'].notna()]['pdf_name'].unique())
                filter_pdf = st.selectbox("Filter by PDF", pdf_options)
            
            with col3:
                days_back = st.slider("Days back", 1, 30, 7)
            
            # Apply filters
            filtered_df = df.copy()
            
            if filter_user != "All":
                filtered_df = filtered_df[filtered_df['username'] == filter_user]
            
            if filter_pdf != "All":
                filtered_df = filtered_df[filtered_df['pdf_name'] == filter_pdf]
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_df = filtered_df[filtered_df['timestamp'] >= cutoff_date]
            
            # Display filtered results
            if not filtered_df.empty:
                display_df = filtered_df.copy()
                display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Safely handle text columns
                if 'question' in display_df.columns:
                    display_df['question'] = display_df['question'].astype(str).str[:100] + '...'
                if 'answer' in display_df.columns:
                    display_df['answer'] = display_df['answer'].astype(str).str[:150] + '...'
                
                # Select available columns
                available_cols = []
                for col in ['timestamp', 'username', 'pdf_name', 'question', 'answer']:
                    if col in display_df.columns:
                        available_cols.append(col)
                
                if available_cols:
                    st.dataframe(
                        display_df[available_cols],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "timestamp": st.column_config.TextColumn("Time", width="medium"),
                            "username": st.column_config.TextColumn("User", width="small"),
                            "pdf_name": st.column_config.TextColumn("PDF", width="medium"),
                            "question": st.column_config.TextColumn("Question", width="large"),
                            "answer": st.column_config.TextColumn("Answer", width="large")
                        }
                    )
                    
                    st.info(f"Showing {len(filtered_df)} results")
                else:
                    st.warning("No display columns available")
            else:
                st.warning("No results found with current filters")
                
        except Exception as e:
            st.error(f"Error processing analytics: {e}")
            st.info("Raw data preview:")
            st.write(df.head() if 'df' in locals() else "No data")
    else:
        st.info("📭 No activity data available yet. Activity will appear here once users start querying PDFs.")