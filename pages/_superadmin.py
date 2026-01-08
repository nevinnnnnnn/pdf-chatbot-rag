import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from core.auth import require_auth
from core.database import (
    get_all_users, get_all_pdfs, get_chat_history, get_system_stats,
    create_user, delete_user, update_user, delete_pdf
)

# Load CSS
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

st.set_page_config(page_title="Super Admin", page_icon="👑", layout="wide")

# Require superadmin authentication
require_auth(required_role="superadmin")

user = st.session_state.user

# Sidebar
with st.sidebar:
    st.markdown(f"""
        <div class='user-info-card' style='background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);'>
            <div class='user-info-label'>Super Admin Panel</div>
            <div class='user-info-name'>{user['username']}</div>
            <div class='user-info-role'>👑 {user['role']}</div>
        </div>
    """, unsafe_allow_html=True)

# Page Header
st.markdown("""
    <div class='page-header' style='background: linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, transparent 100%);'>
        <div class='page-title' style='background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%); 
                                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            👑 Super Admin Dashboard
        </div>
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
        st.markdown("""
            <div class='stat-card'>
                <div class='stat-value'>{}</div>
                <div class='stat-label'>Super Admins</div>
            </div>
        """.format(stats['users'].get('superadmin', 0)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class='stat-card'>
                <div class='stat-value'>{}</div>
                <div class='stat-label'>Admins</div>
            </div>
        """.format(stats['users'].get('admin', 0)), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class='stat-card'>
                <div class='stat-value'>{}</div>
                <div class='stat-label'>Users</div>
            </div>
        """.format(stats['users'].get('user', 0)), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class='stat-card'>
                <div class='stat-value'>{}</div>
                <div class='stat-label'>Total PDFs</div>
            </div>
        """.format(stats['total_pdfs']), unsafe_allow_html=True)
    
    with col5:
        st.markdown("""
            <div class='stat-card'>
                <div class='stat-value'>{}</div>
                <div class='stat-label'>Total Queries</div>
            </div>
        """.format(stats['total_chats']), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👥 Users by Role")
        
        role_data = pd.DataFrame([
            {"Role": role.capitalize(), "Count": count}
            for role, count in stats['users'].items()
        ])
        
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
            font=dict(color='#f1f5f9')
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 Activity (Last 7 Days)")
        
        chats = get_chat_history(limit=1000)
        if chats:
            df = pd.DataFrame(chats)
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            
            # Last 7 days
            last_7_days = [(datetime.now().date() - timedelta(days=i)) for i in range(6, -1, -1)]
            activity = df[df['date'].isin(last_7_days)].groupby('date').size().reindex(last_7_days, fill_value=0)
            
            fig = go.Figure(data=[
                go.Bar(
                    x=[str(d) for d in activity.index],
                    y=activity.values,
                    marker_color='#2563eb'
                )
            ])
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Queries",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f1f5f9')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity data available yet")
    
    st.markdown("---")
    st.markdown("#### 📜 Recent System Activity")
    
    chats = get_chat_history(limit=10)
    if chats:
        df = pd.DataFrame(chats)
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        df['question'] = df['question'].str[:80] + '...'
        df = df[['username', 'pdf_name', 'question', 'timestamp']]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No activity yet")

# ==================== TAB 2: ALL USERS ====================
with tab2:
    st.markdown("### 👥 All Users")
    
    users = get_all_users()
    
    if users:
        df = pd.DataFrame(users)
        df['is_active'] = df['is_active'].map({1: '✅', 0: '❌'})
        df['last_login'] = pd.to_datetime(df['last_login']).dt.strftime('%Y-%m-%d %H:%M')
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d')
        
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
            user_to_modify = st.selectbox("Select User", [u['username'] for u in users])
        
        with col2:
            action = st.selectbox("Action", ["Activate", "Deactivate", "Delete"])
        
        with col3:
            st.write("")
            st.write("")
            if st.button("Execute Action", type="primary", use_container_width=True):
                selected = next(u for u in users if u['username'] == user_to_modify)
                
                if action == "Activate":
                    update_user(selected['id'], is_active=True)
                    st.success(f"✅ Activated: {user_to_modify}")
                    st.rerun()
                elif action == "Deactivate":
                    update_user(selected['id'], is_active=False)
                    st.success(f"✅ Deactivated: {user_to_modify}")
                    st.rerun()
                elif action == "Delete":
                    if selected['role'] == 'superadmin':
                        st.error("❌ Cannot delete superadmin")
                    else:
                        delete_user(selected['id'])
                        st.success(f"✅ Deleted: {user_to_modify}")
                        st.rerun()
    else:
        st.info("No users found")

# ==================== TAB 3: ADMINS ====================
with tab3:
    st.markdown("### 👨‍💼 Admin Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### ➕ Create New Admin")
        
        with st.form("create_admin"):
            admin_username = st.text_input("Username")
            admin_email = st.text_input("Email")
            admin_password = st.text_input("Password", type="password")
            admin_role = st.selectbox("Role", ["admin", "superadmin"])
            
            if st.form_submit_button("Create Admin", type="primary", use_container_width=True):
                if admin_username and admin_email and admin_password:
                    success = create_user(
                        username=admin_username,
                        email=admin_email,
                        password=admin_password,
                        role=admin_role,
                        created_by=user['id']
                    )
                    
                    if success:
                        st.success(f"✅ Admin '{admin_username}' created!")
                        st.rerun()
                    else:
                        st.error("❌ Username/email already exists")
    
    with col2:
        st.markdown("#### 📋 Admin List")
        
        admins = [u for u in get_all_users() if u['role'] in ['admin', 'superadmin']]
        
        if admins:
            df = pd.DataFrame(admins)
            df['is_active'] = df['is_active'].map({1: '✅', 0: '❌'})
            df['last_login'] = pd.to_datetime(df['last_login']).dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(
                df[['username', 'email', 'role', 'is_active', 'last_login']],
                use_container_width=True,
                hide_index=True
            )

# ==================== TAB 4: ALL PDFs ====================
with tab4:
    st.markdown("### 📚 All PDFs")
    
    pdfs = get_all_pdfs()
    
    if pdfs:
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total PDFs", len(pdfs))
        with col2:
            st.metric("Total Pages", sum(p['num_pages'] for p in pdfs))
        with col3:
            st.metric("Total Chunks", sum(p['num_chunks'] for p in pdfs))
        with col4:
            st.metric("Total Images", sum(p['num_images'] for p in pdfs))
        
        st.markdown("---")
        
        # PDF List
        df = pd.DataFrame(pdfs)
        df['file_size'] = df['file_size'].apply(lambda x: f"{x / 1024 / 1024:.2f} MB")
        df['upload_date'] = pd.to_datetime(df['upload_date']).dt.strftime('%Y-%m-%d %H:%M')
        
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
            pdf_to_delete = st.selectbox("Select PDF", [f"{p['id']} - {p['original_name']}" for p in pdfs])
        
        with col2:
            st.write("")
            st.write("")
            if st.button("Delete PDF", type="primary", use_container_width=True):
                pdf_id = int(pdf_to_delete.split(" - ")[0])
                delete_pdf(pdf_id)
                st.success(f"✅ PDF deleted successfully!")
                st.rerun()
    else:
        st.info("📭 No PDFs in the system yet")

# ==================== TAB 5: ANALYTICS ====================
with tab5:
    st.markdown("### 📈 Advanced Analytics")
    
    chats = get_chat_history(limit=1000)
    
    if chats:
        df = pd.DataFrame(chats)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        
        # Row 1: Activity over time
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📅 Daily Activity (Last 30 Days)")
            
            last_30_days = [(datetime.now().date() - timedelta(days=i)) for i in range(29, -1, -1)]
            daily_activity = df[df['date'].isin(last_30_days)].groupby('date').size().reindex(last_30_days, fill_value=0)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[str(d) for d in daily_activity.index],
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
                font=dict(color='#f1f5f9'),
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### ⏰ Hourly Activity Pattern")
            
            hourly_activity = df.groupby('hour').size()
            
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
                font=dict(color='#f1f5f9'),
                xaxis=dict(tickmode='linear', tick0=0, dtick=2)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Row 2: User and PDF analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👥 Most Active Users")
            
            user_activity = df.groupby('username').size().sort_values(ascending=False).head(10)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=user_activity.values,
                y=user_activity.index,
                orientation='h',
                marker_color='#7c3aed'
            ))
            fig.update_layout(
                xaxis_title="Number of Queries",
                yaxis_title="Username",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f1f5f9'),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 📚 Most Queried PDFs")
            
            pdf_activity = df[df['pdf_name'].notna()].groupby('pdf_name').size().sort_values(ascending=False).head(10)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=pdf_activity.values,
                y=pdf_activity.index,
                orientation='h',
                marker_color='#10b981'
            ))
            fig.update_layout(
                xaxis_title="Number of Queries",
                yaxis_title="PDF Name",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f1f5f9'),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Row 3: Detailed activity log
        st.markdown("#### 📜 Detailed Activity Log")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_user = st.selectbox("Filter by User", ["All"] + list(df['username'].unique()))
        
        with col2:
            filter_pdf = st.selectbox("Filter by PDF", ["All"] + list(df[df['pdf_name'].notna()]['pdf_name'].unique()))
        
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
            display_df['question'] = display_df['question'].str[:100] + '...'
            display_df['answer'] = display_df['answer'].str[:150] + '...'
            
            st.dataframe(
                display_df[['timestamp', 'username', 'pdf_name', 'question', 'answer']],
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
            st.warning("No results found with current filters")
    else:
        st.info("📭 No activity data available yet. Activity will appear here once users start querying PDFs.")