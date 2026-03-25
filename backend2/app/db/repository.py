import uuid
from datetime import datetime

from app.db.db import get_connection
from app.services.chart_service import build_visualizations


def _load_query_dataframe(sql_query, row_limit=None):
    if not sql_query:
        return None

    try:
        with get_connection() as con:
            df = con.execute(sql_query).df()
        if row_limit is not None:
            df = df.head(row_limit)
        return df
    except Exception:
        return None


def _load_table_preview(sql_query, row_limit=None):
    df = _load_query_dataframe(sql_query, row_limit=row_limit)
    if df is None or df.empty:
        return None
    return df.to_dict(orient="records")


def _load_visualizations(sql_query):
    df = _load_query_dataframe(sql_query)
    if df is None or df.empty:
        return []
    return build_visualizations(df)

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
        messages = []
        for row in rows:
            messages.append(
                {
                    "role": row[0],
                    "content": row[1],
                    "sql": row[2],
                    "chart": row[3],
                    "data": _load_table_preview(row[2]),
                    "visualizations": _load_visualizations(row[2]),
                }
            )
        return messages

def update_chat_title(chat_id, title):
    with get_connection() as con:
        con.execute(
            "UPDATE chats SET title=? WHERE id=?",
            (title, chat_id)
        )
