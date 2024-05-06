# Description: This file contains the code for the /feedback command.

# Import the required libraries
from disnake.ext import commands
import disnake
import helper.error as error
import settings

# Setup the logger
logger = settings.logging.getLogger('commands')


# This is a test command to check if the bot is working
class Feedback(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command to send feedback to a very specific channel in a very specific server
    @commands.slash_command(description='Send feedback to the developers.')
    async def feedback(
            self,
            interaction: disnake.ApplicationCommandInteraction,
            feedback: str = commands.param(description="Your feedback message.")
    ):
        try:
            logger.info(f"[{interaction.channel.id}] {interaction.author.id}: /feedback ({interaction.id})")

            # Get the feedback channel
            bot = self.bot
            feedback_channel = bot.get_channel(settings.FEEDBACK_CHANNEL_ID)

            # Send the feedback to the feedback channel
            embed = disnake.Embed(
                title="New Feedback",
                description=f"**User:** {interaction.author.mention}\n\n{feedback}",
                color=disnake.Colour(settings.EMBED_COLOR)
            )
            await feedback_channel.send(embed=embed)

            # Send a confirmation message to the user
            embed = disnake.Embed(
                title="Feedback Sent",
                description="Your feedback has been sent successfully!",
                color=disnake.Colour(settings.EMBED_COLOR)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error when sending feedback: {e}")
            await interaction.response.send_message(embed=error.create_error_embed(str(e)), ephemeral=True)


# Add the cog to the bot
def setup(bot):
    bot.add_cog(Feedback(bot))
