import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        database=os.getenv("PGDATABASE", "telegram_bot"),
        user=os.getenv("PGUSER", "your_pg_user"),
        password=os.getenv("PGPASSWORD", "your_pg_password"),
        port=os.getenv("PGPORT", 5432)
    )
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            text TEXT,
            image_file_id TEXT,
            caption TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def insert_message(user_id: str, text: str = None, image_file_id: str = None, caption: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, text, image_file_id, caption) VALUES (%s, %s, %s, %s)",
        (user_id, text, image_file_id, caption)
    )
    conn.commit()
    cursor.close()
    conn.close()

def search_messages(keyword: str):
    """
    Search for text messages (or messages with captions) using a keyword.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = "SELECT * FROM messages WHERE (text ILIKE %s OR caption ILIKE %s) ORDER BY timestamp DESC"
    pattern = f"%{keyword}%"
    cursor.execute(query, (pattern, pattern))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_photo_by_id(photo_id: int, user_id: str):
    """
    Retrieve a photo message by its ID for a given user.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT * FROM messages 
        WHERE id = %s AND user_id = %s AND image_file_id IS NOT NULL
    """
    cursor.execute(query, (photo_id, user_id))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def list_photos(user_id: str):
    """
    List all photo messages for a given user.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT id, caption, timestamp FROM messages 
        WHERE user_id = %s AND image_file_id IS NOT NULL 
        ORDER BY timestamp DESC
    """
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def search_photos_filtered(user_id: str, keyword: str = "", start_date: str = None, end_date: str = None):
    """
    Retrieve photo messages for a user filtered by an optional keyword and/or date range.
    
    Parameters:
      - user_id: The Telegram user ID.
      - keyword: Keyword to search in text or caption (case-insensitive).
      - start_date: ISO date (e.g., '2023-03-01') to filter messages sent on/after this date.
      - end_date: ISO date (e.g., '2023-03-15') to filter messages sent on/before this date.
      
    Returns:
      A list of dictionaries (rows) matching the criteria.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = "SELECT * FROM messages WHERE user_id = %s AND image_file_id IS NOT NULL"
    params = [user_id]
    
    if keyword:
        query += " AND (text ILIKE %s OR caption ILIKE %s)"
        kw = f"%{keyword}%"
        params.extend([kw, kw])
    if start_date:
        query += " AND timestamp >= %s"
        params.append(start_date)
    if end_date:
        query += " AND timestamp <= %s"
        params.append(end_date)
    
    query += " ORDER BY timestamp DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
