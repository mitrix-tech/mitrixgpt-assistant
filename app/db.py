import psycopg
import os
from psycopg_pool import ConnectionPool

DB_NAME = os.environ.get("POSTGRES_DB", "chatmemory")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5433")


def get_connection(as_pool=False):
    if as_pool:
        pool = ConnectionPool(
            # Example configuration
            conninfo=f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
            max_size=20,
        )
        pool.autocommit = True

        return pool
    else:
        conn = psycopg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        conn.autocommit = True

        return conn


# ------------------ Chat CRUD ------------------

def create_chat(title: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat (title) VALUES (%s) RETURNING id;", (title,))
    chat_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return chat_id


def list_chats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at FROM chat ORDER BY created_at DESC;")
    chats = cursor.fetchall()
    cursor.close()
    conn.close()
    return chats


def read_chat(chat_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at FROM chat WHERE id = %s;", (chat_id,))
    chat = cursor.fetchone()
    cursor.close()
    conn.close()
    return chat


def delete_chat(chat_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat WHERE id = %s;", (chat_id,))
    conn.commit()
    cursor.close()
    conn.close()


# ------------------ Source CRUD ------------------

def create_source(name: str, source_text: str, chat_id: int, source_type: str = "document"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sources (name, source_text, type, chat_id) VALUES (%s, %s, %s, %s);",
        (name, source_text, source_type, chat_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def list_sources(chat_id: int, source_type: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    if source_type:
        cursor.execute(
            "SELECT id, name, source_text, type FROM sources WHERE chat_id = %s AND type = %s;",
            (chat_id, source_type)
        )
    else:
        cursor.execute(
            "SELECT id, name, source_text, type FROM sources WHERE chat_id = %s;",
            (chat_id,)
        )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def delete_source(source_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sources WHERE id = %s;", (source_id,))
    conn.commit()
    cursor.close()
    conn.close()


# ------------------ Message CRUD ------------------

def create_message(chat_id: int, sender: str, content: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (chat_id, sender, content) VALUES (%s, %s, %s);",
        (chat_id, sender, content)
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_messages(chat_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sender, content FROM messages WHERE chat_id = %s ORDER BY timestamp ASC;",
        (chat_id,)
    )
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return messages


def delete_messages(chat_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE chat_id = %s;", (chat_id,))
    conn.commit()
    cursor.close()
    conn.close()
