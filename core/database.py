import sqlite3
import bcrypt
from datetime import datetime
from typing import List, Dict, Optional
import os

DB_PATH = "data/users.db"

def init_database():
    """Initialize the database with required tables"""
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,  -- 'superadmin', 'admin', 'user'
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)
    
    # PDFs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pdfs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            uploaded_by INTEGER NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_size INTEGER,
            num_pages INTEGER,
            num_chunks INTEGER,
            num_images INTEGER,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
    """)
    
    # Chat history table
    cursor.execute("""
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
    """)
    
    # Create default superadmin if not exists
    cursor.execute("SELECT * FROM users WHERE role = 'superadmin'")
    if not cursor.fetchone():
        password_hash = bcrypt.hashpw("superadmin123".encode(), bcrypt.gensalt())
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, ("superadmin", "superadmin@system.com", password_hash, "superadmin"))
        print("✅ Default superadmin created (username: superadmin, password: superadmin123)")
    
    conn.commit()
    conn.close()

# ============================================
# USER MANAGEMENT
# ============================================

def create_user(username: str, email: str, password: str, role: str, created_by: int) -> bool:
    """Create a new user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, password_hash, role, created_by))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user and return user info"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, password_hash, role, is_active
        FROM users WHERE username = ?
    """, (username,))
    
    user = cursor.fetchone()
    
    if user and user[5]:  # Check if active
        stored_hash = user[3]
        if bcrypt.checkpw(password.encode(), stored_hash):
            # Update last login
            cursor.execute("""
                UPDATE users SET last_login = ?
                WHERE id = ?
            """, (datetime.now(), user[0]))
            conn.commit()
            conn.close()
            
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "role": user[4]
            }
    
    conn.close()
    return None

def get_all_users(role_filter: Optional[str] = None) -> List[Dict]:
    """Get all users, optionally filtered by role"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if role_filter:
        cursor.execute("""
            SELECT id, username, email, role, created_at, last_login, is_active
            FROM users WHERE role = ?
            ORDER BY created_at DESC
        """, (role_filter,))
    else:
        cursor.execute("""
            SELECT id, username, email, role, created_at, last_login, is_active
            FROM users ORDER BY created_at DESC
        """)
    
    users = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": u[0],
            "username": u[1],
            "email": u[2],
            "role": u[3],
            "created_at": u[4],
            "last_login": u[5],
            "is_active": u[6]
        }
        for u in users
    ]

def update_user(user_id: int, username: str = None, email: str = None, 
                is_active: bool = None) -> bool:
    """Update user information"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if username:
            updates.append("username = ?")
            params.append(username)
        if email:
            updates.append("email = ?")
            params.append(email)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        
        if updates:
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
        return True
    except:
        return False

def delete_user(user_id: int) -> bool:
    """Delete a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# ============================================
# PDF MANAGEMENT
# ============================================

def add_pdf(filename: str, original_name: str, uploaded_by: int,
            file_size: int, num_pages: int, num_chunks: int, num_images: int) -> int:
    """Add a PDF to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO pdfs (filename, original_name, uploaded_by, file_size, 
                         num_pages, num_chunks, num_images)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (filename, original_name, uploaded_by, file_size, num_pages, num_chunks, num_images))
    
    pdf_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pdf_id

def get_all_pdfs(uploaded_by: Optional[int] = None) -> List[Dict]:
    """Get all PDFs, optionally filtered by uploader"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if uploaded_by:
        cursor.execute("""
            SELECT p.id, p.filename, p.original_name, p.uploaded_by, 
                   p.upload_date, p.file_size, p.num_pages, p.num_chunks, 
                   p.num_images, p.is_active, u.username
            FROM pdfs p
            JOIN users u ON p.uploaded_by = u.id
            WHERE p.uploaded_by = ? AND p.is_active = 1
            ORDER BY p.upload_date DESC
        """, (uploaded_by,))
    else:
        cursor.execute("""
            SELECT p.id, p.filename, p.original_name, p.uploaded_by, 
                   p.upload_date, p.file_size, p.num_pages, p.num_chunks, 
                   p.num_images, p.is_active, u.username
            FROM pdfs p
            JOIN users u ON p.uploaded_by = u.id
            WHERE p.is_active = 1
            ORDER BY p.upload_date DESC
        """)
    
    pdfs = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": p[0],
            "filename": p[1],
            "original_name": p[2],
            "uploaded_by": p[3],
            "upload_date": p[4],
            "file_size": p[5],
            "num_pages": p[6],
            "num_chunks": p[7],
            "num_images": p[8],
            "is_active": p[9],
            "uploader_name": p[10]
        }
        for p in pdfs
    ]

def delete_pdf(pdf_id: int) -> bool:
    """Soft delete a PDF"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE pdfs SET is_active = 0 WHERE id = ?", (pdf_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# ============================================
# CHAT HISTORY
# ============================================

def log_chat(user_id: int, pdf_id: Optional[int], question: str, answer: str):
    """Log a chat interaction"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO chat_history (user_id, pdf_id, question, answer)
        VALUES (?, ?, ?, ?)
    """, (user_id, pdf_id, question, answer))
    
    conn.commit()
    conn.close()

def get_chat_history(user_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
    """Get chat history"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("""
            SELECT ch.id, ch.user_id, ch.pdf_id, ch.question, ch.answer, 
                   ch.timestamp, u.username, p.original_name
            FROM chat_history ch
            JOIN users u ON ch.user_id = u.id
            LEFT JOIN pdfs p ON ch.pdf_id = p.id
            WHERE ch.user_id = ?
            ORDER BY ch.timestamp DESC
            LIMIT ?
        """, (user_id, limit))
    else:
        cursor.execute("""
            SELECT ch.id, ch.user_id, ch.pdf_id, ch.question, ch.answer, 
                   ch.timestamp, u.username, p.original_name
            FROM chat_history ch
            JOIN users u ON ch.user_id = u.id
            LEFT JOIN pdfs p ON ch.pdf_id = p.id
            ORDER BY ch.timestamp DESC
            LIMIT ?
        """, (limit,))
    
    history = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": h[0],
            "user_id": h[1],
            "pdf_id": h[2],
            "question": h[3],
            "answer": h[4],
            "timestamp": h[5],
            "username": h[6],
            "pdf_name": h[7]
        }
        for h in history
    ]

# ============================================
# ANALYTICS
# ============================================

def get_system_stats() -> Dict:
    """Get system-wide statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Count users by role
    cursor.execute("SELECT role, COUNT(*) FROM users WHERE is_active = 1 GROUP BY role")
    user_counts = dict(cursor.fetchall())
    
    # Count PDFs
    cursor.execute("SELECT COUNT(*) FROM pdfs WHERE is_active = 1")
    pdf_count = cursor.fetchone()[0]
    
    # Count chats
    cursor.execute("SELECT COUNT(*) FROM chat_history")
    chat_count = cursor.fetchone()[0]
    
    # Recent activity (last 7 days)
    cursor.execute("""
        SELECT COUNT(*) FROM chat_history 
        WHERE timestamp >= datetime('now', '-7 days')
    """)
    recent_chats = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "users": user_counts,
        "total_pdfs": pdf_count,
        "total_chats": chat_count,
        "recent_chats_7d": recent_chats
    }