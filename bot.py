import discord
from discord.ext import commands
from discord.ext.commands import check
import os
from dotenv import load_dotenv

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


def update_count(channel_id, new_count):
    """Update the count in the file for a given channel."""
    with open(CHANNELS_FILE, 'r+') as file:
        lines = file.readlines()
        file.seek(0)
        file.truncate()
        updated = False
        for line in lines:
            cid, count = line.strip().split(':')
            if cid == str(channel_id):
                file.write(f"{cid}:{new_count}\n")
                updated = True
            else:
                file.write(line)
        if not updated:
            file.write(f"{channel_id}:{new_count}\n")


def get_current_count(channel_id):
    """Retrieve the current count for a given channel from the file."""
    with open(CHANNELS_FILE, 'r') as file:
        lines = file.readlines()
    for line in lines:
        cid, count = line.strip().split(':')
        if cid == str(channel_id):
            return int(count)
    return 0  # Default to 0 if not found


async def is_channel_allowed(message):
    """Check if the message channel is in the allowed channels list."""
    with open(CHANNELS_FILE, 'r') as file:
        allowed_channel_ids = [line.strip().split(':')[0] for line in file.readlines()]
    return str(message.channel.id) in allowed_channel_ids


# Event listener for when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')


# Error handler for commands
@bot.event
async def on_command_error(ctx, exception):
    if isinstance(exception, commands.CommandNotFound):
        await ctx.send("Command not recognized.")
    elif isinstance(exception, commands.MissingPermissions):
        await ctx.send("You do not have permission to execute this command.")
    elif isinstance(exception, commands.CheckFailure):
        await ctx.send("This command cannot be used in this channel.")
    else:
        print(f"Unhandled exception: {exception}")


# Error handling general
@bot.event
async def on_error(self, event_method, *args, **kwargs):
    print(f'An error occurred: {event_method}')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    print(f"Received message from {message.author}: '{message.content}' in {message.channel.name}")

    if not message.content.isdigit():
        print("Message is not a digit.")
        await bot.process_commands(message)
        return

    allowed = await is_channel_allowed(message)
    print(f"Is channel allowed? {'Yes' if allowed else 'No'}")

    if allowed:
        current_count = get_current_count(message.channel.id)
        print(f"Current count is {current_count}. Message is {message.content}.")

        try:
            message_number = int(message.content)
            if message_number == current_count + 1:
                update_count(message.channel.id, message_number)
                print(f"Updated count to {message_number}. Adding ✅ reaction.")
                await message.add_reaction(POSITIVE_EMOJI)
            else:

                update_count(message.channel.id, 0)
                print(f"Message number {message_number} does not follow {current_count + 1}. Adding ❌ reaction.")
                await message.add_reaction(NEGATIVE_EMOJI)
                await message.reply(f"You broke the counting! The counting has been reset. Start from 1 again!")

        except ValueError:
            print("Failed to parse message content as integer.")
            pass  # Ignore messages that are not numbers

    await bot.process_commands(message)


# Command to add a channel
@bot.command(description='Add a channel to activate counting in.')
@commands.has_permissions(administrator=True)
async def add_channel(ctx, channel: discord.TextChannel):
    if channel.guild.id != ctx.guild.id:
        await ctx.send(f'Error: {channel.name} is not part of this server.')
        return

    update_count(channel.id, 0)  # Initialize the count at 0 when adding a new channel
    await ctx.send(f'Channel {channel.name} added!')


# Command to delete a channel
@bot.command(description='Remove a channel to deactivate counting in.')
@commands.has_permissions(administrator=True)
async def delete_channel(ctx, channel: discord.TextChannel):
    if channel.guild.id != ctx.guild.id:
        await ctx.send(f'Error: {channel.name} is not part of this server.')
        return

    with open(CHANNELS_FILE, 'r') as file:
        lines = file.readlines()
    with open(CHANNELS_FILE, 'w') as file:
        for line in lines:
            if line.strip().split(':')[0] != str(channel.id):
                file.write(line)
    await ctx.send(f'Channel {channel.name} removed!')


# Bot starts running here
bot.run(discord_token)
