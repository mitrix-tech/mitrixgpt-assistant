import sqlite3

import psycopg
from psycopg_pool import ConnectionPool

from settings import DB_URI


def is_postgres(uri: str) -> bool:
    return uri.startswith("postgresql://") or uri.startswith("postgres://")


def get_connection(as_pool=False):
    """
    Return either a psycopg or an sqlite3 connection object (or pool),
    depending on DB_URI.
    """
    if is_postgres(DB_URI):
        if as_pool:
            pool = ConnectionPool(conninfo=DB_URI, max_size=20)
            pool.autocommit = True
            return pool
        else:
            conn = psycopg.connect(DB_URI)
            conn.autocommit = True
            return conn
    else:
        # Remove the 'sqlite:///' prefix to get the actual filename
        sqlite_path = DB_URI.replace("sqlite:///", "")
        if as_pool:
            # There's no built-in "pool" for sqlite in stdlib, so we can raise an error or do something custom
            raise NotImplementedError("SQLite connection pool not implemented.")
        else:
            conn = sqlite3.connect(sqlite_path, check_same_thread=False)
            # Enable foreign keys in SQLite
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn


def create_tables():
    """
    Create the necessary tables in either Postgres or SQLite.
    """
    if is_postgres(DB_URI):
        _create_postgres_tables()
    else:
        _create_sqlite_tables()


def _create_postgres_tables():
    conn = psycopg.connect(DB_URI)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        source_text TEXT,
        type TEXT DEFAULT 'document',
        chat_id INT,
        FOREIGN KEY (chat_id) REFERENCES chat(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        chat_id INT NOT NULL,
        sender TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(chat_id) REFERENCES chat(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    cur.close()
    conn.close()


def _create_sqlite_tables():
    # Remove the 'sqlite:///' prefix to get the actual filename
    sqlite_path = DB_URI.replace("sqlite:///", "")
    conn = sqlite3.connect(sqlite_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # For SQLite, use INTEGER PRIMARY KEY AUTOINCREMENT
    # instead of SERIAL. Also, ON DELETE CASCADE requires foreign_keys=ON above.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        source_text TEXT,
        type TEXT DEFAULT 'document',
        chat_id INT,
        FOREIGN KEY (chat_id) REFERENCES chat(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INT NOT NULL,
        sender TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(chat_id) REFERENCES chat(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    cur.close()
    conn.close()


# -------------- Chat CRUD ---------------
def create_chat(title: str) -> int:
    conn = get_connection()
    cur = conn.cursor()

    if is_postgres(DB_URI):
        sql = "INSERT INTO chat (title) VALUES (%s) RETURNING id;"
        params = (title,)
        cur.execute(sql, params)
        chat_id = cur.fetchone()[0]
    else:
        # SQLite param placeholders use '?'
        sql = "INSERT INTO chat (title) VALUES (?)"
        cur.execute(sql, (title,))
        chat_id = cur.lastrowid

    conn.commit()
    cur.close()
    conn.close()
    return chat_id


def list_chats():
    conn = get_connection()
    cur = conn.cursor()

    if is_postgres(DB_URI):
        cur.execute("SELECT id, title, created_at FROM chat ORDER BY created_at DESC;")
    else:
        cur.execute("SELECT id, title, created_at FROM chat ORDER BY created_at DESC;")

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def read_chat(chat_id: int):
    conn = get_connection()
    cur = conn.cursor()

    if is_postgres(DB_URI):
        cur.execute("SELECT id, title, created_at FROM chat WHERE id = %s;", (chat_id,))
    else:
        cur.execute("SELECT id, title, created_at FROM chat WHERE id = ?;", (chat_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def delete_chat(chat_id: int):
    conn = get_connection()
    cur = conn.cursor()

    if is_postgres(DB_URI):
        cur.execute("DELETE FROM chat WHERE id = %s;", (chat_id,))
    else:
        cur.execute("DELETE FROM chat WHERE id = ?;", (chat_id,))

    conn.commit()
    cur.close()
    conn.close()


# -------------- Source CRUD ---------------
def create_source(name: str, source_text: str, chat_id: int, source_type: str = "document"):
    conn = get_connection()
    cur = conn.cursor()

    if is_postgres(DB_URI):
        sql = "INSERT INTO sources (name, source_text, type, chat_id) VALUES (%s, %s, %s, %s);"
        cur.execute(sql, (name, source_text, source_type, chat_id))
    else:
        sql = "INSERT INTO sources (name, source_text, type, chat_id) VALUES (?, ?, ?, ?);"
        cur.execute(sql, (name, source_text, source_type, chat_id))

    conn.commit()
    cur.close()
    conn.close()


def list_sources(chat_id: int, source_type: str = None):
    conn = get_connection()
    cur = conn.cursor()
    if source_type:
        if is_postgres(DB_URI):
            sql = "SELECT id, name, source_text, type FROM sources WHERE chat_id = %s AND type = %s;"
            cur.execute(sql, (chat_id, source_type))
        else:
            sql = "SELECT id, name, source_text, type FROM sources WHERE chat_id = ? AND type = ?;"
            cur.execute(sql, (chat_id, source_type))
    else:
        if is_postgres(DB_URI):
            sql = "SELECT id, name, source_text, type FROM sources WHERE chat_id = %s;"
            cur.execute(sql, (chat_id,))
        else:
            sql = "SELECT id, name, source_text, type FROM sources WHERE chat_id = ?;"
            cur.execute(sql, (chat_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def delete_source(source_id: int):
    conn = get_connection()
    cur = conn.cursor()

    if is_postgres(DB_URI):
        cur.execute("DELETE FROM sources WHERE id = %s;", (source_id,))
    else:
        cur.execute("DELETE FROM sources WHERE id = ?;", (source_id,))

    conn.commit()
    cur.close()
    conn.close()


# -------------- Message CRUD ---------------
def create_message(chat_id: int, sender: str, content: str):
    conn = get_connection()
    cur = conn.cursor()

    if is_postgres(DB_URI):
        sql = "INSERT INTO messages (chat_id, sender, content) VALUES (%s, %s, %s);"
        cur.execute(sql, (chat_id, sender, content))
    else:
        sql = "INSERT INTO messages (chat_id, sender, content) VALUES (?, ?, ?);"
        cur.execute(sql, (chat_id, sender, content))

    conn.commit()
    cur.close()
    conn.close()


def get_messages(chat_id: int, limit: int = None):
    conn = get_connection()
    cur = conn.cursor()

    limit_expr = ""
    if isinstance(limit, int):
        limit_expr = f"LIMIT {limit}"

    if is_postgres(DB_URI):
        sql = f"SELECT m.sender, m.content from (SELECT sender, content, timestamp FROM messages WHERE chat_id = %s ORDER BY timestamp DESC {limit_expr}) m ORDER BY m.timestamp ASC;"
        cur.execute(sql, (chat_id,))
    else:
        sql = f"SELECT m.sender, m.content from (SELECT sender, content, timestamp FROM messages WHERE chat_id = ? ORDER BY timestamp DESC {limit_expr}) m ORDER BY m.timestamp ASC;"
        cur.execute(sql, (chat_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def delete_messages(chat_id: int):
    conn = get_connection()
    cur = conn.cursor()

    if is_postgres(DB_URI):
        sql = "DELETE FROM messages WHERE chat_id = %s;"
        cur.execute(sql, (chat_id,))
    else:
        sql = "DELETE FROM messages WHERE chat_id = ?;"
        cur.execute(sql, (chat_id,))

    conn.commit()
    cur.close()
    conn.close()


# For easy CLI usage:
if __name__ == "__main__":
    create_tables()
