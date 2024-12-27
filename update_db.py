import sqlite3
import logging

# ============================
# Logging Configuration
# ============================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def update_database(db_path: str):
    """
    Updates the database schema by adding necessary columns.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Update 'users' table to add 'role' column if not exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'role' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            logger.info("Added 'role' column to 'users' table.")
        else:
            logger.info("'role' column already exists in 'users' table.")

        # Update 'messages' table to add 'channel_message_id' and 'parent_message_id' columns if not exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'channel_message_id' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN channel_message_id INTEGER")
            logger.info("Added 'channel_message_id' column to 'messages' table.")
        else:
            logger.info("'channel_message_id' column already exists in 'messages' table.")
        
        if 'parent_message_id' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN parent_message_id INTEGER")
            logger.info("Added 'parent_message_id' column to 'messages' table.")
        else:
            logger.info("'parent_message_id' column already exists in 'messages' table.")

        conn.commit()
        logger.info("Database schema updated successfully.")

    except sqlite3.Error as e:
        logger.error(f"Error updating database schema: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    DB_PATH = "messages.db"  # Update if necessary
    update_database(DB_PATH)
