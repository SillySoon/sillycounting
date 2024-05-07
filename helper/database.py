import mysql.connector
from mysql.connector import pooling
import settings

# Configure logging for database operations
logger = settings.logging.getLogger("database")


class MariaDBConnectionPool:
    def __init__(self, pool_name='pool', pool_size=5):
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=pool_size,
            pool_reset_session=True,
            host=settings.DATABASE_HOST,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            port=settings.DATABASE_PORT
        )

    def get_connection(self):
        return self.pool.get_connection()

    @staticmethod
    def release_connection(conn):
        if conn is not None:
            try:
                if conn.is_connected():
                    conn.close()
            except Exception as e:
                logger.error(f"Failed to close connection: {e}")
        else:
            logger.error("Attempted to release a None connection")


# Initialize the connection pool
connection_pool = MariaDBConnectionPool()


# Create database connection
def create_connection():
    try:
        return connection_pool.get_connection()
    except Exception as e:
        logger.error(f"Failed to obtain database connection: {e}")
        return None


# Close database connection
def close_connection(conn):
    """ Release a database connection back to the pool."""
    connection_pool.release_connection(conn)


# Set up database
def setup_database():
    """Set up the database and tables and ensure all columns are correct."""
    connection = create_connection()
    if connection is None:
        logger.error("No database connection could be established.")
        return
    else:
        logger.info("Database connection was established successfully.")

    try:
        cursor = connection.cursor()
        # Define your tables and required columns
        tables = {
            'users': {
                'user_id': 'BIGINT PRIMARY KEY',
            },
            'channels': {
                'channel_id': 'BIGINT PRIMARY KEY',
                'count': 'INT DEFAULT 0',  # Default value for count
                'last_user_id': 'BIGINT DEFAULT 0',  # Default value for last_user_id
                'highscore': 'INT DEFAULT 0'  # Default value for highscore
            },
            'channeluser': {
                'channeluser_id': 'INT AUTO_INCREMENT PRIMARY KEY',
                'user_id': 'BIGINT NOT NULL',
                'channel_id': 'BIGINT NOT NULL',
                'count': 'INT NOT NULL DEFAULT 0'  # Default value for count
            }
        }

        # Create tables if they do not exist
        for table_name, columns in tables.items():
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            create_table_sql += ", ".join([f"{col_name} {col_details}" for col_name, col_details in columns.items()])
            create_table_sql += ");"
            cursor.execute(create_table_sql)

        # Check and add missing columns with defaults
        for table_name, columns in tables.items():
            cursor.execute(f"SHOW COLUMNS FROM {table_name};")
            existing_columns = {column[0]: column[1] for column in cursor.fetchall()}
            for col_name, col_details in columns.items():
                if col_name not in existing_columns:
                    alter_table_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_details};"
                    cursor.execute(alter_table_sql)
                    logger.error(f"Added missing column {col_name} with default to {table_name}")

        connection.commit()
        logger.info("Database tables and columns verified successfully.")

    except Exception as e:
        logger.error(f"Failed to create or alter table: {e}")
    finally:
        close_connection(connection)


# Check if the channel is allowed
async def is_channel_allowed(message):
    """Check if the message channel is in the allowed channels list using the database."""
    conn = create_connection()
    if conn is None:
        logger.error("Failed to connect to database when checking channel allowance.")
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM channels WHERE channel_id = %s", (str(message.channel.id),))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Database error when checking if channel is allowed: {e}")
        return False
    finally:
        close_connection(conn)


# Add a channel to the database
def update_count(channel_id, new_count, user_id):
    logger.info(f"{channel_id} requests: update count to {new_count} for user {user_id}")
    """Update the count in the database for a given channel."""

    connection = create_connection()
    sql_string = '''
        UPDATE channels
        SET count = %s, last_user_id = %s
        WHERE channel_id = %s
    '''

    try:
        cur = connection.cursor()
        cur.execute(sql_string, (new_count, user_id, channel_id))
        connection.commit()
    except Exception as e:
        logger.error(f"Failed to update count: {e}")
        print(e)
    finally:
        close_connection(connection)


# Add a channel to the database
def add_channel(channel_id):
    logger.info(f"{channel_id} requests: add channel")
    conn = create_connection()
    sql = '''
        INSERT INTO channels(channel_id, count, last_user_id, highscore)
        VALUES(%s, 0, 0, 0)
    '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to add channel: {e}")
        print(e)
    finally:
        close_connection(conn)


# Remove a channel from the database
def remove_channel(channel_id):
    logger.info(f"{channel_id} requests: remove channel")
    conn = create_connection()
    sql = '''
        DELETE FROM channels
        WHERE channel_id = %s
    '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to remove channel: {e}")
        print(e)
    finally:
        close_connection(conn)


# Check a channel is in the database
def check_channel(channel_id):
    logger.info(f"{channel_id} requests: check channel")
    conn = create_connection()
    sql = '''
        SELECT channel_id
        FROM channels
        WHERE channel_id = %s
    '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        row = cur.fetchone()
        if row:
            return True
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)
    return False  # Default to False if not found


# Check a user is in the database
def check_user(user_id):
    logger.info(f"{user_id} requests: check user")
    conn = create_connection()
    sql = '''
        SELECT user_id
        FROM users WHERE
        user_id = %s
    '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (user_id,))
        row = cur.fetchone()
        if row:
            return True
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)
    return False  # Default to False if not found


# Add a user to the database
def add_user(user_id):
    logger.info(f"{user_id} requests: add user")
    conn = create_connection()
    sql = '''
        INSERT INTO users(user_id)
        VALUES(%s)
    '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (user_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to add user: {e}")
        print(e)
    finally:
        close_connection(conn)


# Update the count for a user in a channel, count is always + 1
def update_user_count(channel_id, user_id):
    logger = logging.getLogger('database')
    logger.info(f"{channel_id} requests: update user count for {user_id}")
    conn = create_connection()
    try:
        with conn.cursor() as cur:
            # First, attempt to fetch the current count
            select_sql = '''
                SELECT count
                FROM channeluser
                WHERE user_id = %s AND channel_id = %s
            '''
            cur.execute(select_sql, (user_id, channel_id))
            row = cur.fetchone()
            cur.fetchall()  # Clear any remaining results from the cursor

            if row:
                new_count = row[0] + 1
                update_sql = '''
                    UPDATE channeluser
                    SET count = %s
                    WHERE user_id = %s AND channel_id = %s
                '''
                cur.execute(update_sql, (new_count, user_id, channel_id))
            else:
                insert_sql = '''
                    INSERT INTO channeluser (user_id, channel_id, count)
                    VALUES (%s, %s, 1)
                '''
                cur.execute(insert_sql, (user_id, channel_id))
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update user count: {e}")
        print(e)
    finally:
        close_connection(conn)


# Get the highscore for a channel
def get_highscore(channel_id):
    logger.info(f"{channel_id} requests: get highscore")
    """Retrieve the highscore for a given channel from the database."""
    conn = create_connection()
    sql = '''
        SELECT highscore
        FROM channels
        WHERE channel_id = %s
    '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        row = cur.fetchone()
        if row:
            return row[0]
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)
    return 0  # Default to 0 if not found


# Get top 10 highscores of all channels
def get_top_channel_highscores():
    logger.info(f"requests: get top highscores")
    """Retrieve the highscore for a given channel from the database."""
    conn = create_connection()
    sql = '''
        SELECT channel_id, highscore
        FROM channels
        ORDER BY highscore
        DESC LIMIT 10
    '''
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)
    return []  # Default to 0 if not found


# Get Top 10 User Highscores of 1 channel
def get_top_user_highscores(channel_id):
    logger.info(f"{channel_id} requests: get top user highscores")
    """Retrieve the highscore for a given channel from the database."""
    conn = create_connection()
    sql = '''
        SELECT user_id, count
        FROM channeluser
        WHERE channel_id = %s
        ORDER BY count
        DESC LIMIT 10
    '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)
    return []  # Default to 0 if not found


# Get top 10 users in all channels
def get_top_users():
    logger.info(f"requests: get top users")
    """Retrieve the highscore for a given channel from the database."""
    conn = create_connection()
    sql = '''
        SELECT user_id, SUM(count) as total_count 
        FROM channeluser 
        GROUP BY user_id 
        ORDER BY total_count 
        DESC LIMIT 10
    '''

    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)
    return []  # Default to 0 if not found


# Update the highscore for a channel
def update_highscore(channel_id, new_highscore):
    logger.info(f"{channel_id} requests: update highscore to {new_highscore}")
    conn = create_connection()

    """Update the highscore in the database for a given channel."""
    sql = '''
        UPDATE channels
        SET highscore = %s
        WHERE channel_id = %s
    '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (new_highscore, channel_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to update highscore: {e}")
        print(e)
    finally:
        close_connection(conn)


# update all highscores, if current count is higher than highscore, update highscore
def update_all_highscores():
    logger.info("Requests: Update all highscores")
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
            logger.info(f"Updated highscores for {cur.rowcount} channels")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        close_connection(conn)


# Get the current count and last user ID for a channel
def get_current_count(channel_id):
    logger.info(f"{channel_id} requests: get current count")
    """Retrieve the current count and last user ID for a given channel from the database."""
    conn = create_connection()
    sql = '''
        SELECT count, last_user_id
        FROM channels
        WHERE channel_id = %s
    '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id,))
        row = cur.fetchone()
        if row:
            return row[0], row[1]
    except Exception as e:
        print(e)
    finally:
        close_connection(conn)
    return 0, None  # Default to 0 and None if not found
