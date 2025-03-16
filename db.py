import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_connection():
    """
    Create a connection to the PostgreSQL database using connection parameters from environment variables.
    """
    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        database=os.getenv("PGDATABASE", "telegram_bot"),
        user=os.getenv("PGUSER", "your_pg_user"),
        password=os.getenv("PGPASSWORD", "your_pg_password"),
        port=os.getenv("PGPORT", 5432)
    )
    return conn

def init_db():
    """
    Initialize the database by creating the messages table if it doesn't exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    conn.commit()
    cursor.close()
    conn.close()

def insert_message(user_id: str, text: str):
    """
    Insert a new message into the messages table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, text) VALUES (%s, %s)",
        (user_id, text)
    )
    conn.commit()
    cursor.close()
    conn.close()

def search_messages(keyword: str):
    """
    Search for messages that contain the keyword (case-insensitive) and return the results as dictionaries.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = "SELECT * FROM messages WHERE text ILIKE %s ORDER BY timestamp DESC"
    pattern = f"%{keyword}%"
    cursor.execute(query, (pattern,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
