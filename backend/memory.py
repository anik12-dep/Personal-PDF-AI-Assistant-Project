
import sqlite3
import uuid
from pathlib import Path

# Database location
DB_PATH = Path(__file__).resolve().parent / "chat_memory.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


# Create database tables
def initialize_db():

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT 'New Conversation',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id)
                REFERENCES conversations(id)
            )
        """)

        # Safe migration for existing databases
        columns = [
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(conversations)"
            ).fetchall()
        ]

        if "title" not in columns:
            conn.execute("""
                ALTER TABLE conversations
                ADD COLUMN title TEXT DEFAULT 'New Conversation'
            """)


# Create a new conversation
def create_conversation():

    conversation_id = str(uuid.uuid4())

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversations (id, title)
            VALUES (?, ?)
            """,
            (conversation_id, "New Conversation")
        )

    return conversation_id


# Update conversation title
def update_conversation_title(conversation_id, title):

    with get_connection() as conn:
        conn.execute("""
            UPDATE conversations
            SET title = ?
            WHERE id = ?
        """, (title, conversation_id))


# Get conversation title
def get_conversation_title(conversation_id):

    with get_connection() as conn:

        row = conn.execute("""
            SELECT title
            FROM conversations
            WHERE id = ?
        """, (conversation_id,)).fetchone()

    return row[0] if row else "New Conversation"


# Load previous conversation history
def get_history(conversation_id):

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
        """, (conversation_id,)).fetchall()

    return [
        {"role": role, "content": content}
        for role, content in rows
    ]


# Save a message
def save_message(conversation_id, role, content):

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO messages
            (conversation_id, role, content)
            VALUES (?, ?, ?)
        """, (conversation_id, role, content))


# List all conversations
def list_conversations():

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT id, title, created_at
            FROM conversations
            ORDER BY created_at DESC
        """).fetchall()

    return rows
