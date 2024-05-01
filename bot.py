import disnake
import logging
import sqlite3
import os
from logging.handlers import TimedRotatingFileHandler
from disnake.ext import commands, tasks
from dotenv import load_dotenv

# Import your database module
import helper.database as db

# Load the environment variables from the .env file
load_dotenv()

# Accessing the environment variables
discord_token = os.getenv('DISCORD_TOKEN')
command_prefix = os.getenv('COMMAND_PREFIX')

# Initialize the Bot with command prefix and intents
intents = disnake.Intents.default()
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
    interval=1,  # Every 1 day
    backupCount=31  # Keep 1 month of logs
)
log_handler.setFormatter(logging.Formatter('%(levelname)s - %(asctime)s - %(message)s'))
log_handler.setLevel(logging.INFO)

# Setup the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Use `logger` to log messages
logger.info("[START] Bot is starting up...")


async def is_channel_allowed(message):
    """Check if the message channel is in the allowed channels list using the database."""
    conn = db.create_connection()
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
        db.close_connection(conn)


# Event listener for when the bot is ready
@bot.event
async def on_ready():
    logger.info("[BOT] Bot is starting up and preparing database...")
    db.setup_database()
    logger.info(f'[BOT] Logged on as {bot.user}!')
    update_status.start()
    print("Bot ready!")


@tasks.loop(minutes=30)
async def update_status():
    activity = disnake.Game(name=f'{command_prefix}help')
    await bot.change_presence(activity=activity, status=disnake.Status.online)


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
        if isinstance(message, disnake.Message):
            channel = message.channel
            try:
                await channel.send("```An unexpected error occurred. Please contact the administrator.```")
            except disnake.DiscordException:
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
        current_count, last_user_id = db.get_current_count(message.channel.id)
        logger.info(f"[{message.channel.id}] {message.author.id}: '{message.content}'")

        try:
            message_number = int(message.content)
            if message_number == current_count + 1 and str(message.author.id) != last_user_id:
                db.update_count(message.channel.id, message_number, message.author.id)
                await message.add_reaction(POSITIVE_EMOJI)
            else:
                if str(message.author.id) == last_user_id:
                    db.update_count(message.channel.id, 0, 0)
                    await message.add_reaction(NEGATIVE_EMOJI)
                    await message.reply("```You can't count twice in a row! Starting from 1 again.```")
                else:
                    db.update_count(message.channel.id, 0, 0)
                    await message.add_reaction(NEGATIVE_EMOJI)
                    await message.reply(f"```The Number should be {current_count + 1}. Starting from 1 again.```")

                """Check if current highscore is less than new highscore and update it."""
                current_highscore = db.get_highscore(message.channel.id)

                if current_count <= current_highscore:
                    await message.channel.send(f"```Current highscore: {current_highscore}. Try to beat it!```")
                    return
                await message.channel.send(f"```New highscore: {current_count}!```")
                db.update_highscore(message.channel.id, current_count)
        except ValueError:
            pass  # Ignore messages that are not numbers

    await bot.process_commands(message)


# Command to add a channel
@bot.slash_command(description='Add a channel to activate counting in.')
@commands.has_permissions(administrator=True)
async def add_channel(interaction: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
    if channel.guild.id != interaction.guild.id:
        await interaction.send(f'```Error: {channel.name} is not part of this server.```')
        return

    conn = db.create_connection()
    if conn is None:
        await interaction.send("```Database connection failed.```")
        return

    logger.info(f"[{interaction.channel.id}] {interaction.author.id}: '{interaction.id}'")

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM channels WHERE channel_id = ?", (str(channel.id),))
        if cursor.fetchone():
            await interaction.send(f'```Error: Channel {channel.name} is already added.```')
        else:
            db.add_channel(str(channel.id))
            await interaction.send(f'```Channel {channel.name} added!```')
            await channel.send(f'```Counting activated! Start counting by typing 1.```')
    finally:
        db.close_connection(conn)


# Command to delete a channel
@bot.slash_command(description='Remove a channel to deactivate counting in.')
@commands.has_permissions(administrator=True)
async def delete_channel(interaction: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
    if channel.guild.id != interaction.guild.id:
        await interaction.send(f'```Error: {channel.name} is not part of this server.```')
        return

    conn = db.create_connection()
    if conn is None:
        await interaction.send("```Database connection failed.```")
        return

    logger.info(f"[{interaction.channel.id}] {interaction.author.id}: '{interaction.id}'")

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM channels WHERE channel_id = ?", (str(channel.id),))
        if not cursor.fetchone():
            await interaction.send(f'```Error: Channel {channel.name} not activated.```')
        else:
            cursor.execute("DELETE FROM channels WHERE channel_id = ?", (str(channel.id),))
            conn.commit()
            await interaction.send(f'```Channel {channel.name} removed!```')
    finally:
        db.close_connection(conn)


# Command to show the highscore
@bot.slash_command(description='Show the highscore of the current channel.')
async def highscore(interaction: disnake.ApplicationCommandInteraction):
    if not await is_channel_allowed(interaction):
        await interaction.send("```This channel is not activated for counting.```")
        return

    logger.info(f"[{interaction.channel.id}] {interaction.author.id}: '{interaction.id}'")

    current_highscore = db.get_highscore(interaction.channel.id)
    await interaction.send(f'```Current highscore: {current_highscore}```')


# Command to reset the highscore
@bot.slash_command(description='Reset the highscore of the current channel.')
@commands.has_permissions(administrator=True)
async def reset_highscore(interaction: disnake.ApplicationCommandInteraction):
    if not await is_channel_allowed(interaction):
        await interaction.send("```This channel is not activated for counting.```")
        return

    logger.info(f"[{interaction.channel.id}] {interaction.author.id}: '{interaction.id}'")

    db.update_highscore(interaction.channel.id, 0)
    await interaction.send("```Highscore reset.```")


# Set counter
@bot.slash_command(description='Set the current counter of current channel.')
@commands.has_permissions(administrator=True)
async def set_counter(interaction: disnake.ApplicationCommandInteraction, count: int):
    if not await is_channel_allowed(interaction):
        await interaction.send("```This channel is not activated for counting.```")
        return

    logger.info(f"[{interaction.channel.id}] {interaction.author.id}: '{interaction.id}'")

    db.update_count(interaction.channel.id, count, 0)  # Reset last_user_id since it's an admin override
    await interaction.send(f'```Count set to {count}```')


# Bot starts running here
bot.run(discord_token)
