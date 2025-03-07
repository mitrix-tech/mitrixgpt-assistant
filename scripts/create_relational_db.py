import psycopg2


def create_tables():
    conn = psycopg2.connect(
        dbname="chatmemory",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5433",
    )
    cursor = conn.cursor()

    # Create chat table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create sources table with ON DELETE CASCADE on the foreign key
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            source_text TEXT,
            type TEXT DEFAULT 'document',
            chat_id INT,
            FOREIGN KEY (chat_id) REFERENCES chat(id) ON DELETE CASCADE
        );
    """)

    # Create messages table with ON DELETE CASCADE on the foreign key
    cursor.execute("""
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
    cursor.close()
    conn.close()
    print("Tables created successfully in Postgres.")


if __name__ == "__main__":
    create_tables()
