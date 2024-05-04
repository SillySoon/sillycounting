import sqlite3
from sqlite3 import Connection
from queue import Queue
import logging
import settings

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
connection_pool = SQLiteConnectionPool(settings.DATABASE_PATH)


# Create database connection
def create_connection():
    """ Get a database connection from the pool."""
    return connection_pool.get_connection()


# Close database connection
def close_connection(conn):
    """ Release a database connection back to the pool."""
    connection_pool.release_connection(conn)


# Set up the database
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
        # Create the 'users' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY
            );
        ''')

        # Create the 'channels' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                count INTEGER,
                last_user_id TEXT
            );
        ''')

        # Create the 'channeluser' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channeluser (
                channeluser_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                count INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
            );
        ''')
        connection.commit()
        logger.info("[DATABASE] Database table created successfully.")

        # Check if all columns of users exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        required_columns = ["user_id", "username"]
        for column in required_columns:
            logger.info(f"[DATABASE] Checking for column {column}")
            if column not in columns:
                if column == "user_id":
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column} INTEGER")
                connection.commit()
                logger.info(f"[DATABASE] Column {column} added successfully.")

        # Check if all columns of channels exist
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

        # Check if all columns of channeluser exist
        cursor.execute("PRAGMA table_info(channeluser)")
        columns = [column[1] for column in cursor.fetchall()]
        required_columns = ["channeluser_id", "user_id", "channel_id", "count"]
        for column in required_columns:
            logger.info(f"[DATABASE] Checking for column {column}")
            if column not in columns:
                if column == "channeluser_id":
                    cursor.execute(f"ALTER TABLE channeluser ADD COLUMN {column} INTEGER PRIMARY KEY AUTOINCREMENT")
                elif column == "user_id":
                    cursor.execute(f"ALTER TABLE channeluser ADD COLUMN {column} TEXT")
                elif column == "channel_id":
                    cursor.execute(f"ALTER TABLE channeluser ADD COLUMN {column} TEXT")
                else:
                    cursor.execute(f"ALTER TABLE channeluser ADD COLUMN {column} INTEGER")
                connection.commit()
                logger.info(f"[DATABASE] Column {column} added successfully.")

    except sqlite3.Error as e:
        logger.error(f"[DATABASE] Failed to create or alter table: {e}")
    finally:
        close_connection(connection)


# Check if the channel is allowed
async def is_channel_allowed(message):
    """Check if the message channel is in the allowed channels list using the database."""
    conn = create_connection()
    if conn is None:
        logger.error("[BOT] Failed to connect to database when checking channel allowance.")
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM channels WHERE channel_id = ?", (str(message.channel.id),))
        return cursor.fetchone() is not None
    except sqlite3.Error as e:
        logger.error(f"[BOT] Database error when checking if channel is allowed: {e}")
        return False
    finally:
        close_connection(conn)


# Add a channel to the database
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


# Add a channel to the database
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


# Remove a channel from the database
def remove_channel(channel_id):
    logger.info(f"[BOT] {channel_id} requests: remove channel")
    conn = create_connection()
    sql = ''' DELETE FROM channels WHERE channel_id = ? '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"[BOT] Failed to remove channel: {e}")
        print(e)
    finally:
        close_connection(conn)


# Check a channel is in the database
def check_channel(channel_id):
    logger.info(f"[BOT] {channel_id} requests: check channel")
    conn = create_connection()
    sql = ''' SELECT channel_id FROM channels WHERE channel_id = ? '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        row = cur.fetchone()
        if row:
            return True
    except sqlite3.Error as e:
        print(e)
    finally:
        close_connection(conn)
    return False  # Default to False if not found


# Check a user is in the database
def check_user(user_id):
    logger.info(f"[BOT] {user_id} requests: check user")
    conn = create_connection()
    sql = ''' SELECT user_id FROM users WHERE user_id = ? '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (user_id,))
        row = cur.fetchone()
        if row:
            return True
    except sqlite3.Error as e:
        print(e)
    finally:
        close_connection(conn)
    return False  # Default to False if not found


# Add a user to the database
def add_user(user_id):
    logger.info(f"[BOT] {user_id} requests: add user")
    conn = create_connection()
    sql = ''' INSERT INTO users(user_id) VALUES(?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"[BOT] Failed to add user: {e}")
        print(e)
    finally:
        close_connection(conn)


# Update the count for a user in a channel, count is always + 1
def update_user_count(channel_id, user_id):
    logger.info(f"[BOT] {channel_id} requests: update user count for {user_id}")
    conn = create_connection()
    sql = ''' SELECT count FROM channeluser WHERE user_id = ? AND channel_id = ? '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (user_id, channel_id))
        row = cur.fetchone()
        if row:
            new_count = row[0] + 1
            sql = ''' UPDATE channeluser SET count = ? WHERE user_id = ? AND channel_id = ? '''
            cur.execute(sql, (new_count, user_id, channel_id))
            conn.commit()
        else:
            sql = ''' INSERT INTO channeluser(user_id, channel_id, count) VALUES(?, ?, 1) '''
            cur.execute(sql, (user_id, channel_id))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"[BOT] Failed to update user count: {e}")
        print(e)
    finally:
        close_connection(conn)


# Get the highscore for a channel
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


# Get top 10 highscores of all channels
def get_top_channel_highscores():
    logger.info(f"[BOT] requests: get top highscores")
    """Retrieve the highscore for a given channel from the database."""
    conn = create_connection()
    sql = ''' SELECT channel_id, highscore FROM channels ORDER BY highscore DESC LIMIT 10 '''
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(e)
    finally:
        close_connection(conn)
    return []  # Default to 0 if not found


# Get Top 10 User Highscores of 1 channel
def get_top_user_highscores(channel_id):
    logger.info(f"[BOT] {channel_id} requests: get top user highscores")
    """Retrieve the highscore for a given channel from the database."""
    conn = create_connection()
    sql = ''' SELECT user_id, count FROM channeluser WHERE channel_id = ? ORDER BY count DESC LIMIT 10 '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(e)
    finally:
        close_connection(conn)
    return []  # Default to 0 if not found


# Get top 10 users in all channels
def get_top_users():
    logger.info(f"[BOT] requests: get top users")
    """Retrieve the highscore for a given channel from the database."""
    conn = create_connection()
    sql = ''' SELECT user_id, SUM(count) as total_count FROM channeluser GROUP BY user_id ORDER BY total_count DESC LIMIT 10 '''
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(e)
    finally:
        close_connection(conn)
    return []  # Default to 0 if not found


# Update the highscore for a channel
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


# update all highscores, if current count is higher than highscore, update highscore
def update_all_highscores():
    logging.info("[BOT] Requests: Update all highscores")
    conn = create_connection()

    # Directly update the highscore in the database where count is greater than highscore
    update_sql = '''
        UPDATE channels
        SET highscore = count
        WHERE count > highscore;
    '''
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(update_sql)
            conn.commit()
            logging.info(f"[DATABASE] Updated highscores for {cur.rowcount} channels")
    except sqlite3.Error as e:
        logging.error(f"An error occurred: {e}")
    finally:
        close_connection(conn)


# Get the current count and last user ID for a channel
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
