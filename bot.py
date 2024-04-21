import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import logging
import sqlite3

# Load the environment variables from the .env file
load_dotenv()

# Accessing the environment variables
discord_token = os.getenv('DISCORD_TOKEN')

# Initialize the Bot with command prefix and intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

POSITIVE_EMOJI = '<:positive:1203089362833768468>'
NEGATIVE_EMOJI = '<:negative:1203089360644476938>'

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, filename='bot_log.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Now you can use the logging
logger = logging.getLogger(__name__)

# Example of using logger
logger.info("Bot is starting up...")


def create_connection(db_file):
    """Create a database connection to a SQLite database specified by db_file."""
    try:
        conn = sqlite3.connect(db_file)
        logger.info(f"Connected to SQLite database: {db_file}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database due to: {e}")
        return None


def setup_database():
    """Set up the database and tables."""
    database = "bot_database.db"
    connection = create_connection(database)
    if connection is None:
        logger.error("No database connection could be established.")
        return
    else:
        logger.info("Database connection was established successfully.")

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
        logger.info("Database table created successfully.")
    except sqlite3.Error as e:
        logger.error(f"Failed to create table: {e}")
    finally:
        connection.close()


def update_count(channel_id, new_count, user_id):
    """Update the count in the database for a given channel."""
    database = "bot_database.db"
    conn = create_connection(database)
    sql = ''' REPLACE INTO channels(channel_id, count, last_user_id)
              VALUES(?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (channel_id, new_count, user_id))
        conn.commit()
    except sqlite3.Error as e:
        print(e)
    finally:
        conn.close()


def get_current_count(channel_id):
    """Retrieve the current count and last user ID for a given channel from the database."""
    database = "bot_database.db"
    conn = create_connection(database)
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
        conn.close()
    return 0, None  # Default to 0 and None if not found


async def is_channel_allowed(message):
    """Check if the message channel is in the allowed channels list using the database."""
    database = "bot_database.db"
    conn = create_connection(database)
    if conn is None:
        logger.error("Failed to connect to database when checking channel allowance.")
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM channels WHERE channel_id = ?", (str(message.channel.id),))
        return cursor.fetchone() is not None
    except sqlite3.Error as e:
        logger.error(f"Database error when checking if channel is allowed: {e}")
        return False
    finally:
        conn.close()


# Event listener for when the bot is ready
@bot.event
async def on_ready():
    logger.info("Bot is starting up and preparing database...")
    setup_database()
    logger.info(f'Logged on as {bot.user}!')
    update_status.start()
    print("Bot ready!")


@tasks.loop(minutes=30)
async def update_status():
    activity = discord.Game(name=f"Counting on {len(bot.guilds)} Servers")
    await bot.change_presence(activity=activity, status=discord.Status.online)


# Error handler for commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not recognized.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to execute this command.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("This command cannot be used in this channel.")
    else:
        logger.error(f"Unhandled exception: {error}")
        await ctx.send("An unexpected error occurred.")
        raise error  # Optionally re-raise the error if you want it to propagate


# Error handling general
@bot.event
async def on_error(event_method, *args, **kwargs):
    logger.error(f'```An error occurred in {event_method}```')
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

    if await is_channel_allowed(message):
        current_count, last_user_id = get_current_count(message.channel.id)

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

        except ValueError:
            pass  # Ignore messages that are not numbers

    await bot.process_commands(message)


# Command to add a channel
@bot.command(description='Add a channel to activate counting in.')
@commands.has_permissions(administrator=True)
async def add_channel(ctx, channel: discord.TextChannel):
    if channel.guild.id != ctx.guild.id:
        await ctx.send(f'```Error: {channel.name} is not part of this server.```')
        return

    database = "bot_database.db"
    conn = create_connection(database)
    if conn is None:
        await ctx.send("Database connection failed.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM channels WHERE channel_id = ?", (str(channel.id),))
        if cursor.fetchone():
            await ctx.send(f'```Error: Channel {channel.name} is already added.```')
        else:
            update_count(channel.id, 0, 0)  # Initialize the count at 0 when adding a new channel
            await ctx.send(f'```Channel {channel.name} added!```')
            await channel.send(f'```Counting activated! Start counting by typing 1.```')
    finally:
        conn.close()


# Command to delete a channel
@bot.command(description='Remove a channel to deactivate counting in.')
@commands.has_permissions(administrator=True)
async def delete_channel(ctx, channel: discord.TextChannel):
    if channel.guild.id != ctx.guild.id:
        await ctx.send(f'```Error: {channel.name} is not part of this server.```')
        return

    database = "bot_database.db"
    conn = create_connection(database)
    if conn is None:
        await ctx.send("Database connection failed.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM channels WHERE channel_id = ?", (str(channel.id),))
        if not cursor.fetchone():
            await ctx.send(f'```Error: Channel {channel.name} not activated.```')
        else:
            cursor.execute("DELETE FROM channels WHERE channel_id = ?", (str(channel.id),))
            conn.commit()
            await ctx.send(f'```Channel {channel.name} removed!```')
    finally:
        conn.close()


# Set counter
@bot.command(description='Set the current counter of current channel.')
@commands.has_permissions(administrator=True)
async def set_counter(ctx, count: int):  # Automatically handles type conversion
    if not await is_channel_allowed(ctx.message):
        await ctx.send("This channel is not activated for counting.")
        return

    update_count(ctx.channel.id, count, 0)  # Reset last_user_id since it's an admin override
    await ctx.send(f'```Count set to {count}```')


# Bot starts running here
bot.run(discord_token)
