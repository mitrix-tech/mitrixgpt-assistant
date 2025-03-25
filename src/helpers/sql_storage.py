from typing import Optional

import psycopg
from context import AppContext


class SqlStorage:
    """
    Provides methods for creating tables and performing CRUD operations
    on chat, sources, and messages in PostgreSQL, using UUID as the ID type.
    """

    def __init__(self, app_context: AppContext):
        self.app_context = app_context
        self.logger = app_context.logger
        self.conninfo = self.app_context.env_vars.DB_URI

    def get_connection(self) -> psycopg.Connection:
        """
        Returns a new psycopg connection (autocommit = True).
        """
        conn = psycopg.connect(self.conninfo)
        conn.autocommit = True
        return conn

    def create_tables(self):
        """
        Creates the necessary tables in Postgres with UUID primary keys,
        and ensures that 'uuid-ossp' extension is created if needed.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create table: chat
                cur.execute("""
                CREATE TABLE IF NOT EXISTS chat (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)

                # Create table: messages
                cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    chat_id UUID NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(chat_id) REFERENCES chat(id) ON DELETE CASCADE
                );
                """)

        self.logger.info("Tables have been created or already exist.")

    # -------------- Chat CRUD ---------------
    def create_chat(self, title: Optional[str] = None) -> str:
        """
        Inserts a new row into 'chat', returning the new chat's UUID.
        If 'title' is provided, store it; otherwise leave it NULL.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if title:
                    # Insert with a title
                    sql = """
                        INSERT INTO chat (title)
                        VALUES (%s)
                        RETURNING id;
                    """
                    cur.execute(sql, (title,))
                else:
                    # No title supplied
                    sql = "INSERT INTO chat DEFAULT VALUES RETURNING id;"
                    cur.execute(sql)
                chat_id = cur.fetchone()[0]  # The UUID from RETURNING id
                return str(chat_id)

    def list_chats(self):
        """
        Returns a list of all chats (id, title, created_at), ordered by creation time descending.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, created_at FROM chat ORDER BY created_at DESC;")
                rows = cur.fetchall()
                return rows  # list of tuples (UUID, title, created_at)

    def read_chat(self, chat_id: str):
        """
        Reads a single chat row by UUID, or returns None if not found.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, created_at FROM chat WHERE id = %s;", (chat_id,))
                row = cur.fetchone()
                return row  # (UUID, title, created_at) or None

    def delete_chat(self, chat_id: str):
        """
        Deletes a single chat by UUID. Will cascade-delete messages.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chat WHERE id = %s;", (chat_id,))

    # -------------- Message CRUD ---------------
    def create_message(self, chat_id: str, sender: str, content: str):
        """
        Inserts a new message row for a given chat_id.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                sql = "INSERT INTO messages (chat_id, sender, content) VALUES (%s, %s, %s);"
                cur.execute(sql, (chat_id, sender, content))

    def get_messages(self, chat_id: str, limit: int = None):
        """
        Retrieve messages for the given chat_id, in ascending timestamp order.
        If limit is provided, only retrieve that many messages (from the most recent).
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                limit_expr = ""
                if isinstance(limit, int):
                    limit_expr = f"LIMIT {limit}"

                sql = f"""
                SELECT m.sender, m.content
                FROM (
                    SELECT sender, content, timestamp
                    FROM messages
                    WHERE chat_id = %s
                    ORDER BY timestamp DESC
                    {limit_expr}
                ) m
                ORDER BY m.timestamp ASC;
                """
                cur.execute(sql, (chat_id,))
                rows = cur.fetchall()
                return rows

    def delete_messages(self, chat_id: str):
        """
        Deletes all messages for a given chat_id.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                sql = "DELETE FROM messages WHERE chat_id = %s;"
                cur.execute(sql, (chat_id,))
