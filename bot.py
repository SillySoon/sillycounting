import discord
import logging
import sqlite3
import os
from logging.handlers import TimedRotatingFileHandler
from discord.ext import commands, tasks
from dotenv import load_dotenv
from sqlite3 import Connection
from queue import Queue

# Load the environment variables from the .env file
load_dotenv()

# Accessing the environment variables
discord_token = os.getenv('DISCORD_TOKEN')
command_prefix = os.getenv('COMMAND_PREFIX')
database_path = os.getenv('DATABASE_PATH')

# Initialize the Bot with command prefix and intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix=command_prefix, intents=intents)

POSITIVE_EMOJI = '<:positive:1232460365183582239>'
NEGATIVE_EMOJI = '<:negative:1232460363954651177>'

# Setup basic configuration for logging
os.makedirs('./logs', exist_ok=True)  # Ensure the directory for logs exists

# Setup handler for rotating logs daily
log_handler = TimedRotatingFileHandler(
    filename='./logs/log',  # Base file name
    when='midnight',  # Rotate at midnight
    interval=1,       # Every 1 day
    backupCount=31     # Keep 1 month of logs
)
log_handler.setFormatter(logging.Formatter('%(levelname)s - %(asctime)s - %(message)s'))
log_handler.setLevel(logging.INFO)

# Setup the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Use `logger` to log messages
logger.info("[START] Bot is starting up...")


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


connection_pool = SQLiteConnectionPool(database_path)


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
    conn = create_connection()
    sql = ''' UPDATE channels SET count = ?, last_user_id = ? WHERE channel_id = ? '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (new_count, user_id, channel_id))
        conn.commit()
    except sqlite3.Error as e:
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


# Event listener for when the bot is ready
@bot.event
async def on_ready():
    logger.info("[BOT] Bot is starting up and preparing database...")
    setup_database()
    logger.info(f'[BOT] Logged on as {bot.user}!')
    update_status.start()
    print("Bot ready!")


@tasks.loop(minutes=30)
async def update_status():
    activity = discord.Game(name=f'{command_prefix}help')
    await bot.change_presence(activity=activity, status=discord.Status.online)


# Error handler for commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply("```Command not recognized.```")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.reply("```You do not have permission to execute this command.```")
    elif isinstance(error, commands.CheckFailure):
        await ctx.reply("```This command cannot be used in this channel.```")
    else:
        logger.error(f"Unhandled exception: {error}")
        await ctx.reply("```An unexpected error occurred.```")
        raise error  # Optionally re-raise the error if you want it to propagate


# Error handling general
@bot.event
async def on_error(event_method, *args, **kwargs):
    logger.error(f'An error occurred in {event_method}')
    # Extracting the channel from args if possible
    if args:
        message = args[0]  # Assuming that the first arg is the message
        if isinstance(message, discord.Message):
            channel = message.channel
            try:
                await channel.send("```An unexpected error occurred. Please contact the administrator.```")
            except discord.DiscordException:
                pass  # In case the bot doesn't have permission to send messages in the channel
    # Log to console or a file if necessary
    logger.error(f"Error in {event_method}: {args} {kwargs}")  # Make sure to set up a logger


@bot.event
async def on_message(message):
    if message.author == bot.user or not message.content.isdigit():
        await bot.process_commands(message)
        return

    print(f"[{message.channel.id}] {message.author.id}: '{message.content}'")

    if await is_channel_allowed(message):
        current_count, last_user_id = get_current_count(message.channel.id)
        logger.info(f"[{message.channel.id}] {message.author.id}: '{message.content}'")

        try:
            message_number = int(message.content)
            if message_number == current_count + 1 and str(message.author.id) != last_user_id:
                update_count(message.channel.id, message_number, message.author.id)
                await message.add_reaction(POSITIVE_EMOJI)
            else:
                if str(message.author.id) == last_user_id:
                    update_count(message.channel.id, 0, 0)
                    await message.add_reaction(NEGATIVE_EMOJI)
                    await message.reply("```You can't count twice in a row! Starting from 1 again.```")
                else:
                    update_count(message.channel.id, 0, 0)
                    await message.add_reaction(NEGATIVE_EMOJI)
                    await message.reply(f"```The Number should be {current_count + 1}. Starting from 1 again.```")

                """Check if current highscore is less than new highscore and update it."""
                current_highscore = get_highscore(message.channel.id)

                if current_count <= current_highscore:
                    await message.channel.send(f"```Current highscore: {current_highscore}. Try to beat it!```")
                    return
                await message.channel.send(f"```New highscore: {current_count}!```")
                update_highscore(message.channel.id, current_count)
        except ValueError:
            pass  # Ignore messages that are not numbers

    await bot.process_commands(message)


# Command to add a channel
@bot.command(description='Add a channel to activate counting in.')
@commands.has_permissions(administrator=True)
async def add_channel(ctx, channel: discord.TextChannel):
    if channel.guild.id != ctx.guild.id:
        await ctx.reply(f'```Error: {channel.name} is not part of this server.```')
        return

    conn = create_connection()
    if conn is None:
        await ctx.reply("```Database connection failed.```")
        return

    logger.info(f"[{ctx.channel.id}] {ctx.author.id}: '{ctx.content}'")

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM channels WHERE channel_id = ?", (str(channel.id),))
        if cursor.fetchone():
            await ctx.reply(f'```Error: Channel {channel.name} is already added.```')
        else:
            update_count(channel.id, 0, 0)  # Initialize the count at 0 when adding a new channel
            await ctx.reply(f'```Channel {channel.name} added!```')
            await channel.send(f'```Counting activated! Start counting by typing 1.```')
    finally:
        close_connection(conn)


# Command to delete a channel
@bot.command(description='Remove a channel to deactivate counting in.')
@commands.has_permissions(administrator=True)
async def delete_channel(ctx, channel: discord.TextChannel):
    if channel.guild.id != ctx.guild.id:
        await ctx.reply(f'```Error: {channel.name} is not part of this server.```')
        return

    conn = create_connection()
    if conn is None:
        await ctx.reply("```Database connection failed.```")
        return

    logger.info(f"[{ctx.channel.id}] {ctx.author.id}: '{ctx.content}'")

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM channels WHERE channel_id = ?", (str(channel.id),))
        if not cursor.fetchone():
            await ctx.reply(f'```Error: Channel {channel.name} not activated.```')
        else:
            cursor.execute("DELETE FROM channels WHERE channel_id = ?", (str(channel.id),))
            conn.commit()
            await ctx.reply(f'```Channel {channel.name} removed!```')
    finally:
        close_connection(conn)


# Command to show the highscore
@bot.command(description='Show the highscore of the current channel.')
async def highscore(ctx):
    if not await is_channel_allowed(ctx.message):
        await ctx.reply("```This channel is not activated for counting.```")
        return

    logger.info(f"[{ctx.channel.id}] {ctx.author.id}: '{ctx.content}'")

    current_highscore = get_highscore(ctx.channel.id)
    await ctx.reply(f'```Current highscore: {current_highscore}```')


# Command to reset the highscore
@bot.command(description='Reset the highscore of the current channel.')
@commands.has_permissions(administrator=True)
async def reset_highscore(ctx):
    if not await is_channel_allowed(ctx.message):
        await ctx.reply("```This channel is not activated for counting.```")
        return

    logger.info(f"[{ctx.channel.id}] {ctx.author.id}: '{ctx.content}'")

    update_highscore(ctx.channel.id, 0)
    await ctx.reply("```Highscore reset.```")


# Set counter
@bot.command(description='Set the current counter of current channel.')
@commands.has_permissions(administrator=True)
async def set_counter(ctx, count: int):  # Automatically handles type conversion
    if not await is_channel_allowed(ctx.message):
        await ctx.reply("```This channel is not activated for counting.```")
        return

    logger.info(f"[{ctx.channel.id}] {ctx.author.id}: '{ctx.content}'")

    update_count(ctx.channel.id, count, 0)  # Reset last_user_id since it's an admin override
    await ctx.reply(f'```Count set to {count}```')


# Bot starts running here
bot.run(discord_token)
