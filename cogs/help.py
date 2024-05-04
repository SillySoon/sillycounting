# Description: This file contains the code for the help command.

# Import the required libraries
from disnake.ext import commands
import disnake
import helper.error as error
import settings

# Setup the logger
logger = settings.logging.getLogger('commands')


# This is a test command to check if the bot is working
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Command for help
    @commands.slash_command(description='Show the help message.')
    async def help(
            self,
            interaction: disnake.ApplicationCommandInteraction
    ):
        try:
            logger.info(f"[{interaction.channel.id}] {interaction.author.id}: /help ({interaction.id})")

            embed = disnake.Embed(
                title="SillyCounting Help",
                description="[] = Needed argument\n() = Optional argument",
                color=disnake.Colour(settings.EMBED_COLOR)
            )
            embed.add_field(name="`/help`", value="Show this help message")
            embed.add_field(name="`/enable [channel]`", value="Enable counting in the current channel")
            embed.add_field(name="`/disable [channel]`", value="Disable counting in the current channel")
            embed.add_field(name="`/highscore`", value="Show the current highscore")
            embed.add_field(name="`/reset_highscore`", value="Reset the highscore")
            embed.add_field(name="`/leaderboard [action]`", value="Show some leaderboard information")
            embed.add_field(name="`/feedback [feedback]`", value="Send feedback to the developers")
            embed.add_field(name="`/eval_number [expression]`", value="Evaluate a number")
            await interaction.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error when showing help: {e}")
            await interaction.send(embed=error.create_error_embed(str(e)), ephemeral=True)


# Add the cog to the bot
def setup(bot):
    bot.add_cog(Help(bot))
