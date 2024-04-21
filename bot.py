import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import logging

# Load the environment variables from the .env file
load_dotenv()

# Accessing the environment variables
discord_token = os.getenv('DISCORD_TOKEN')

# Initialize the Bot with command prefix and intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

CHANNELS_FILE = 'channels_data.txt'
open(CHANNELS_FILE, 'a').close()  # Ensure the file exists

POSITIVE_EMOJI = '<:positive:1203089362833768468>'
NEGATIVE_EMOJI = '<:negative:1203089360644476938>'

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, filename='bot_log.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Now you can use the logging
logger = logging.getLogger(__name__)

# Example of using logger
logger.info("Bot is starting up...")


def update_count(channel_id, new_count, user_id):
    """Update the count in the file for a given channel."""
    with open(CHANNELS_FILE, 'r+') as file:
        lines = file.readlines()
        file.seek(0)
        file.truncate()
        updated = False
        for line in lines:
            cid, count, last_user_id = line.strip().split(':')
            if cid == str(channel_id):
                file.write(f"{cid}:{new_count}:{user_id}\n")
                updated = True
            else:
                file.write(line)
        if not updated:
            file.write(f"{channel_id}:{new_count}:{user_id}\n")


def get_current_count(channel_id):
    """Retrieve the current count and last user ID for a given channel from the file."""
    with open(CHANNELS_FILE, 'r') as file:
        lines = file.readlines()
    for line in lines:
        cid, count, last_user_id = line.strip().split(':')
        if cid == str(channel_id):
            return int(count), last_user_id
    return 0, None  # Default to 0 and None if not found


async def is_channel_allowed(message):
    """Check if the message channel is in the allowed channels list."""
    with open(CHANNELS_FILE, 'r') as file:
        allowed_channel_ids = [line.strip().split(':')[0] for line in file.readlines()]
    return str(message.channel.id) in allowed_channel_ids


# Event listener for when the bot is ready
@bot.event
async def on_ready():
    print("Bot is ready.")
    logger.info(f'Logged on as {bot.user}!')
    update_status.start()


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

    with open(CHANNELS_FILE, 'r') as file:
        existing_channels = [line.strip().split(':')[0] for line in file.readlines()]
    if str(channel.id) in existing_channels:
        await ctx.send(f'```Error: Channel {channel.name} is already added.```')
        return

    update_count(channel.id, 0, 0)  # Initialize the count at 0 when adding a new channel
    await ctx.send(f'```Channel {channel.name} added!```')
    await channel.send(f'```Counting activated! Start counting by typing 1.```')


# Command to delete a channel
@bot.command(description='Remove a channel to deactivate counting in.')
@commands.has_permissions(administrator=True)
async def delete_channel(ctx, channel: discord.TextChannel):
    if channel.guild.id != ctx.guild.id:
        await ctx.send(f'```Error: {channel.name} is not part of this server.```')
        return

    with open(CHANNELS_FILE, 'r') as file:
        lines = file.readlines()
        channel_ids = [line.strip().split(':')[0] for line in lines]

    if str(channel.id) not in channel_ids:
        await ctx.send(f'```Error: Channel {channel.name} not activated.```')
        return

    with open(CHANNELS_FILE, 'w') as file:
        for line in lines:
            if line.strip().split(':')[0] != str(channel.id):
                file.write(line)

    await ctx.send(f'```Channel {channel.name} removed!```')


# Set counter
@bot.command(description='Set the current counter of current channel.')
@commands.has_permissions(administrator=True)
async def set_counter(ctx, count: int):  # Automatically handles type conversion
    if await is_channel_allowed(ctx):
        update_count(ctx.channel.id, count, 0)  # Reset last_user_id since it's an admin override
        await ctx.send(f'```Count set to {count}```')


# Bot starts running here
bot.run(discord_token)
