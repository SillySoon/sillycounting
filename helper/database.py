import sqlite3
from sqlite3 import Connection
from queue import Queue
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Database path from .env
DATABASE_PATH = os.getenv('DATABASE_PATH')

# Configure logging for database operations
logger = logging.getLogger(__name__)


class SQLiteConnectionPool:
    def __init__(self, db_file, max_connections=5):
        self.db_file = db_file
        self.pool = Queue(max_connections)
        for _ in range(max_connections):
            self.pool.put(sqlite3.connect(db_file, check_same_thread=False))

    def get_connection(self) -> Connection:
        return self.pool.get()

    def release_connection(self, conn: Connection):
        self.pool.put(conn)


# Initialize the connection pool
connection_pool = SQLiteConnectionPool(DATABASE_PATH)


def create_connection():
    """ Get a database connection from the pool."""
    return connection_pool.get_connection()


def close_connection(conn):
    """ Release a database connection back to the pool."""
    connection_pool.release_connection(conn)


def setup_database():
    """Set up the database and tables."""
    connection = create_connection()
    if connection is None:
        logger.error("[DATABASE] No database connection could be established.")
        return
    else:
        logger.info("[DATABASE] Database connection was established successfully.")

    try:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                count INTEGER,
                last_user_id TEXT
            )
        ''')
        connection.commit()
        logger.info("[DATABASE] Database table created successfully.")

        # Check if all columns exist
        cursor.execute("PRAGMA table_info(channels)")
        columns = [column[1] for column in cursor.fetchall()]
        required_columns = ["channel_id", "count", "last_user_id", "highscore"]
        for column in required_columns:
            logger.info(f"[DATABASE] Checking for column {column}")
            if column not in columns:
                if column == "highscore":
                    cursor.execute(f"ALTER TABLE channels ADD COLUMN {column} INTEGER")
                elif column == "count":
                    cursor.execute(f"ALTER TABLE channels ADD COLUMN {column} INTEGER")
                else:
                    cursor.execute(f"ALTER TABLE channels ADD COLUMN {column} TEXT")
                connection.commit()
                logger.info(f"[DATABASE] Column {column} added successfully.")
    except sqlite3.Error as e:
        logger.error(f"[DATABASE] Failed to create or alter table: {e}")
    finally:
        close_connection(connection)


def update_count(channel_id, new_count, user_id):
    logger.info(f"[BOT] {channel_id} requests: update count to {new_count} for user {user_id}")
    """Update the count in the database for a given channel."""

    connection = create_connection()
    sql_string = ''' UPDATE channels SET count = ?, last_user_id = ? WHERE channel_id = ? '''

    try:
        cur = connection.cursor()
        cur.execute(sql_string, (new_count, user_id, channel_id))
        connection.commit()
    except sqlite3.Error as e:
        logger.error(f"[BOT] Failed to update count: {e}")
        print(e)
    finally:
        close_connection(connection)


def add_channel(channel_id):
    logger.info(f"[BOT] {channel_id} requests: add channel")
    conn = create_connection()
    sql = ''' INSERT INTO channels(channel_id, count, last_user_id, highscore) VALUES(?, 0, 0, 0) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"[BOT] Failed to add channel: {e}")
        print(e)
    finally:
        close_connection(conn)


def get_highscore(channel_id):
    logger.info(f"[BOT] {channel_id} requests: get highscore")
    """Retrieve the highscore for a given channel from the database."""
    conn = create_connection()
    sql = ''' SELECT highscore FROM channels WHERE channel_id = ? '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        row = cur.fetchone()
        if row:
            return row[0]
    except sqlite3.Error as e:
        print(e)
    finally:
        close_connection(conn)
    return 0  # Default to 0 if not found


def update_highscore(channel_id, new_highscore):
    logger.info(f"[BOT] {channel_id} requests: update highscore to {new_highscore}")
    conn = create_connection()

    """Update the highscore in the database for a given channel."""
    sql = ''' UPDATE channels SET highscore = ? WHERE channel_id = ? '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (new_highscore, channel_id))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to update highscore: {e}")
        print(e)
    finally:
        close_connection(conn)


def get_current_count(channel_id):
    logger.info(f"[BOT] {channel_id} requests: get current count")
    """Retrieve the current count and last user ID for a given channel from the database."""
    conn = create_connection()
    sql = ''' SELECT count, last_user_id FROM channels WHERE channel_id = ? '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        row = cur.fetchone()
        if row:
            return row[0], row[1]
    except sqlite3.Error as e:
        print(e)
    finally:
        close_connection(conn)
    return 0, None  # Default to 0 and None if not found
