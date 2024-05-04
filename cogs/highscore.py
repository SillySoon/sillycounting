# Description: This file contains the command to enable the counting function in a channel.

# Import the required libraries
from datetime import datetime
from disnake.ext import commands, tasks
import disnake
import helper.database as db
import helper.error as error
import settings

# Setup the logger
logger = settings.logging.getLogger('commands')

highscore_change_timestamp = 0


# This is a test command to check if the bot is working
class Highscore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_all_highscores.start()

    # Task to update all highscores every 60 minutes
    @tasks.loop(minutes=60)
    async def update_all_highscores(self):
        db.update_all_highscores()
        global highscore_change_timestamp  # Use the global variable
        highscore_change_timestamp = datetime.now().timestamp()

    # Command to show the highscore
    @commands.slash_command(description='Show the highscore of the current channel.')
    async def highscore(
            self,
            interaction: disnake.ApplicationCommandInteraction
    ):
        try:
            logger.info(f"[{interaction.channel.id}] {interaction.author.id}: /highscore ({interaction.id})")

            # Check if the channel is allowed for counting
            if not await db.is_channel_allowed(interaction):
                embed = disnake.Embed(
                    title="Sorry!",
                    description=f"This channel is not activated for counting.",
                    color=disnake.Colour(settings.EMBED_COLOR)
                )
                await interaction.send(embed=embed, ephemeral=True)
                return

            # Get the current highscore from the database
            current_highscore = db.get_highscore(interaction.channel.id)
            embed = disnake.Embed(
                title="Highscore",
                description=(f"The current highscore is `{current_highscore}`"
                             f"\nLast automatic change: <t:{int(highscore_change_timestamp)}:R>"),
                color=disnake.Colour(settings.EMBED_COLOR)
            )
            embed.set_footer(text="The highscore is updated every 60 minutes.")
            await interaction.send(embed=embed, ephemeral=True)
        # Catch any exceptions and send an error message
        except Exception as e:
            logger.error(f"Error when getting highscore: {e}")
            await interaction.send(embed=error.create_error_embed(str(e)), ephemeral=True)

    # Command to reset the highscore
    @commands.slash_command(description='Reset the highscore of the current channel.')
    @commands.has_permissions(administrator=True)
    async def reset_highscore(
            self,
            interaction: disnake.ApplicationCommandInteraction
    ):
        try:
            logger.info(f"[{interaction.channel.id}] {interaction.author.id}: /reset_highscore ({interaction.id})")

            # Check if the channel is allowed for counting
            if not await db.is_channel_allowed(interaction):
                embed = disnake.Embed(
                    title="Sorry!",
                    description=f"This channel is not activated for counting.",
                    color=disnake.Colour(settings.EMBED_COLOR)
                )
                await interaction.send(embed=embed, ephemeral=True)
                return

            # Reset the highscore in the database
            db.update_highscore(interaction.channel.id, 0)
            embed = disnake.Embed(
                title="Highscore Reset",
                description=f"Highscore successfully reset!",
                color=disnake.Colour(settings.EMBED_COLOR)
            )
            embed.set_footer(text="Your thoughts? Use /feedback to share!")
            await interaction.send(embed=embed)
        # Catch any exceptions and send an error message
        except Exception as e:
            logger.error(f"Error when resetting highscore: {e}")
            await interaction.send(embed=error.create_error_embed(str(e)), ephemeral=True)


# Add the cog to the bot
def setup(bot):
    bot.add_cog(Highscore(bot))
