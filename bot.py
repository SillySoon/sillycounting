# Description: Main file for the bot. Contains the main logic for the bot.
# Created by: SillySoon https://github.com/SillySoon


# import own modules
import helper.database as db
import helper.error as error
import helper.eval as eval
import settings

# Importing necessary libraries
import disnake
from disnake.ext import commands, tasks
from random import choice

# Initialize the Bot with command prefix and intents
intents = disnake.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.AutoShardedBot(command_prefix=settings.COMMAND_PREFIX, intents=intents)

# Setup the logger
logger = settings.logging.getLogger('bot')

# Use `logger` to log messages
logger.info("Bot is starting up...")

# Emojis for reactions
POSITIVE_EMOJI = '<:positive:1232460365183582239>'
NEGATIVE_EMOJI = '<:negative:1232460363954651177>'


# Event listener for when the bot is ready
@bot.event
async def on_ready():
    # Prepare the database
    logger.info("Bot is starting up and preparing database...")
    db.setup_database()

    # Start the tasks
    update_status.start()

    # Log a message to the console
    logger.info(f'Logged on as {bot.user} with {bot.shard_count} shards!')


# Load Cogs On Start
for cog_file in settings.COGS_DIR.glob('*.py'):
    cog_name = f"cogs.{cog_file.stem}"
    try:
        bot.load_extension(cog_name)
        logger.debug(f"Loaded cog: {cog_name}")
    except Exception as e:
        logger.error(f"Failed to load cog: {cog_name}\n{e}")


# Task to update the bot's status every 30 minutes
@tasks.loop(minutes=30)
async def update_status():
    status_list = ["/help"]
    activity = disnake.Game(name=choice(status_list))
    await bot.change_presence(activity=activity, status=disnake.Status.online)


# Event listener for when a message is sent
@bot.event
async def on_message(message):
    if message.author == bot.user:
        await bot.process_commands(message)
        return

    if await db.is_channel_allowed(message):
        try:
            # Attempt to evaluate the content of the message as a math expression
            message_number = eval.safe_eval(message.content)
            if isinstance(message_number, float):
                message_number = round(message_number)  # Round the result to the nearest integer for counting
        except:
            # Fallback if the message is not a valid expression, ignore it
            await bot.process_commands(message)
            return

        try:
            current_count, last_user_id = db.get_current_count(message.channel.id)

            logger.info(f"[{message.channel.id}] {message.author.id}: {message.content} ({message_number})")

            if message_number == current_count + 1 and str(message.author.id) != last_user_id:
                # Update the count in the database
                db.update_count(message.channel.id, message_number, message.author.id)

                # Update user count
                if not db.check_user(str(message.author.id)):
                    db.add_user(message.author.id)
                db.update_user_count(message.channel.id, message.author.id)

                # Add a reaction to the message
                await message.add_reaction(POSITIVE_EMOJI)
            else:
                if str(message.author.id) == last_user_id:
                    db.update_count(message.channel.id, 0, 0)
                    await message.add_reaction(NEGATIVE_EMOJI)
                    embed = disnake.Embed(
                        title="You cannot count twice in a row!",
                        description="Starting from `1` again.",
                        color=disnake.Colour(settings.EMBED_COLOR)
                    )
                    embed.set_footer(text="Your thoughts? Use /feedback to share!")
                    await message.reply(embed=embed)
                else:
                    db.update_count(message.channel.id, 0, 0)
                    await message.add_reaction(NEGATIVE_EMOJI)
                    embed = disnake.Embed(
                        title=f"The number was {current_count + 1}",
                        description=f"Starting from `1` again.",
                        color=disnake.Colour(settings.EMBED_COLOR)
                    )
                    embed.set_footer(text="Your thoughts? Use /feedback to share!")
                    await message.reply(embed=embed)

                """Check if current highscore is less than new highscore and update it."""
                current_highscore = db.get_highscore(message.channel.id)

                if current_count <= current_highscore:
                    embed = disnake.Embed(
                        title="Better luck next time!",
                        description=f"Current highscore is {current_highscore}. Try to beat it!",
                        color=disnake.Colour(settings.EMBED_COLOR)
                    )
                    await message.channel.send(embed=embed)
                    return

                db.update_highscore(message.channel.id, current_count)
                embed = disnake.Embed(
                    title="New highscore!",
                    description=f"We reached a highscore of `{current_count}`!",
                    color=disnake.Colour(settings.EMBED_COLOR)
                )
                await message.channel.send(embed=embed)
        except ValueError:
            pass  # Ignore messages that are not numbers

    await bot.process_commands(message)


# Event listener for when a message is deleted
@bot.event
async def on_message_delete(message):
    if message.author == bot.user:
        return

    try:
        evaluated_message = eval.safe_eval(message.content)
        if not isinstance(evaluated_message, (int, float)):  # Check if it's a number
            return
    except Exception:
        return  # Ignore if the message content is not a valid expression or causes an error

    # Check if the channel is allowed for counting
    if await db.is_channel_allowed(message):
        current_count, last_user_id = db.get_current_count(message.channel.id)

        # Check if the message matched the current count
        if not evaluated_message == current_count:
            return  # Ignore if the message was not the current count

        embed = disnake.Embed(
            title="Number Deleted",
            description=f"<@{message.author.id}> deleted a message!\nCurrent count is `{current_count}`.",
            color=disnake.Colour(settings.EMBED_COLOR)
        )
        await message.channel.send(embed=embed)


# Event listener for when a message is edited
@bot.event
async def on_message_edit(before, after):
    if before.author == bot.user:
        return

    try:
        evaluated_before = eval.safe_eval(before.content)
        if not isinstance(evaluated_before, (int, float)):  # Check if it's a number
            return
    except Exception:
        return  # Ignore if the before message content is not a valid expression or causes an error

    # Check if the channel is allowed for counting
    if await db.is_channel_allowed(before):
        current_count, last_user_id = db.get_current_count(before.channel.id)

        # Check if the message matched the current count
        if not evaluated_before == current_count:
            return  # Ignore if the message was not the current count

        embed = disnake.Embed(
            title="Number Edited",
            description=f"<@{before.author.id}> edited a message!\nCurrent count is `{current_count}`.",
            color=disnake.Colour(settings.EMBED_COLOR)
        )
        await before.channel.send(embed=embed)


# Slash command error handler
@bot.event
async def on_slash_command_error(interaction: disnake.ApplicationCommandInteraction, e):
    if isinstance(e, commands.MissingPermissions):
        # You can customize this message as per your need
        embed = disnake.Embed(
            title="Permission Denied",
            description="You do not have the necessary permissions to use this command.",
            color=disnake.Colour(settings.EMBED_COLOR)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        # Log other errors as they are not permission-related
        logger.error(f"Error executing command: {e}")
        # Send a general error message
        await interaction.response.send_message(embed=error.create_error_embed(e), ephemeral=True)


# Bot starts running here
bot.run(settings.DISCORD_TOKEN, reconnect=True)
