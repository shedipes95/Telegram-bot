import sqlite3

def get_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row  # Allow access to columns by name
    return conn

def init_db():
    """Initialize the database and create tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()

def insert_message(user_id: str, text: str):
    """Insert a new message into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (user_id, text) VALUES (?, ?)", (user_id, text))
    conn.commit()
    conn.close()

def search_messages(keyword: str):
    """
    Search for messages that contain the keyword.

    Args:
        keyword (str): The search term.

    Returns:
        list: A list of sqlite3.Row objects where the message text matches the keyword.
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM messages WHERE text LIKE ? ORDER BY timestamp DESC"
    pattern = f"%{keyword}%"
    cursor.execute(query, (pattern,))
    rows = cursor.fetchall()
    conn.close()
    return rows
