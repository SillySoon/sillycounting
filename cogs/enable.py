# Description: This file contains the command to enable the counting function in a channel.
# The command is only available to users with the administrator permission.

# Import the required libraries
from disnake.ext import commands
import disnake
import helper.database as db
import helper.error as error
import settings

# Setup the logger
logger = settings.logging.getLogger('commands')


# This is a test command to check if the bot is working
class Enable(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Command to add a channel
    @commands.slash_command(description='Enables the counting function in XYZ channel.')
    @commands.has_permissions(administrator=True)
    async def enable(
            self,
            interaction: disnake.ApplicationCommandInteraction,
            channel: disnake.TextChannel
    ):
        try:
            logger.info(f"[{interaction.channel.id}] {interaction.author.id}: /enable {channel.id} ({interaction.id})")

            if db.check_channel(str(channel.id)):
                embed = disnake.Embed(
                    title="Sorry!",
                    description=f"Channel <#{channel.id}> is already a counting channel.",
                    color=disnake.Colour(settings.EMBED_COLOR)
                )
                await interaction.send(embed=embed, ephemeral=True)
                return

            db.add_channel(str(channel.id))
            embed = disnake.Embed(
                title="Channel Added",
                description=f"Channel <#{channel.id}> successfully added!",
                color=disnake.Colour(settings.EMBED_COLOR)
            )
            await interaction.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error when adding channel: {e}")
            await interaction.send(embed=error.create_error_embed(str(e)), ephemeral=True)


# Add the cog to the bot
def setup(bot):
    bot.add_cog(Enable(bot))
