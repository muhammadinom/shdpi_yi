import sqlite3

DB_NAME = "bot_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        student_id TEXT,
        full_name TEXT,
        faculty TEXT,
        group_name TEXT,
        phone TEXT,
        balls INTEGER DEFAULT 0
    )
    """)
    
    # Sertifikatlar jadvali
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        cert_title TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """)
    
    conn.commit()
    conn.close()

def add_user(user_id, full_name, faculty, group_name, phone, student_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, student_id, full_name, faculty, group_name, phone, balls)
    VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT balls FROM users WHERE user_id = ?), 0))
    """, (user_id, student_id, full_name, faculty, group_name, phone, user_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, student_id, full_name, faculty, group_name, phone, balls FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            "user_id": user[0],
            "student_id": user[1],
            "full_name": user[2],
            "faculty": user[3],
            "group": user[4],
            "phone": user[5],
            "balls": user[6]
        }
    return None

def add_certificate(user_id, cert_title):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO certificates (user_id, cert_title) VALUES (?, ?)", (user_id, cert_title))
    cursor.execute("UPDATE users SET balls = balls + 15 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_user_certs(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT cert_title FROM certificates WHERE user_id = ?", (user_id,))
    certs = cursor.fetchall()
    conn.close()
    return [c[0] for c in certs]

def get_last_student_id():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return 1001 + count