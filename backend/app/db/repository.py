import uuid
from datetime import datetime
from app.db.db import get_connection

def init_tables():
    with get_connection() as con:

        con.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id VARCHAR PRIMARY KEY,
            title VARCHAR,
            created_at TIMESTAMP
        )
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id VARCHAR PRIMARY KEY,
            chat_id VARCHAR,
            role VARCHAR,
            content VARCHAR,
            sql_query VARCHAR,
            chart_path VARCHAR,
            created_at TIMESTAMP,
            FOREIGN KEY(chat_id) REFERENCES chats(id)
        )
        """)

def create_chat():
    chat_id = str(uuid.uuid4())
    with get_connection() as con:
        con.execute(
            "INSERT INTO chats VALUES (?, ?, ?)",
            (chat_id, "New Chat", datetime.now())
        )
    return chat_id

def get_chats():
    with get_connection() as con:
        rows = con.execute(
            "SELECT * FROM chats ORDER BY created_at DESC"
        ).fetchall()
        return [{"id": row[0], "title": row[1], "time": str(row[2])} for row in rows]

def delete_chat(chat_id):
    with get_connection() as con:
        con.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        con.execute("DELETE FROM chats WHERE id=?", (chat_id,))
        # Check if chat was actually removed
        result = con.execute("SELECT COUNT(*) FROM chats WHERE id=?", (chat_id,)).fetchone()
        return result[0] == 0

def save_message(chat_id, role, content, sql=None, chart=None):
    msg_id = str(uuid.uuid4())
    with get_connection() as con:
        con.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?)",
            (msg_id, chat_id, role, content, sql, chart, datetime.now())
        )

def get_messages(chat_id):
    with get_connection() as con:
        rows = con.execute(
            "SELECT role, content, sql_query, chart_path FROM messages WHERE chat_id=? ORDER BY created_at",
            (chat_id,)
        ).fetchall()
        return [{"role": row[0], "content": row[1], "sql": row[2], "chart": row[3]} for row in rows]

def update_chat_title(chat_id, title):
    with get_connection() as con:
        con.execute(
            "UPDATE chats SET title=? WHERE id=?",
            (title, chat_id)
        )