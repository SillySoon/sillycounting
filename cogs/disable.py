# This file contains the command to remove a channel from the database
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
class Disable(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Command to remove a channel
    @commands.slash_command(description='Disables the counting function in XYZ channel.')
    @commands.has_permissions(administrator=True)
    async def disable(
            self,
            interaction: disnake.ApplicationCommandInteraction,
            channel: disnake.TextChannel
    ):
        try:
            logger.info(f"[{interaction.channel.id}] {interaction.author.id}: /disable {channel.id} ({interaction.id})")

            if not db.check_channel(str(channel.id)):
                embed = disnake.Embed(
                    title="Sorry!",
                    description=f"Channel <#{channel.id}> is not a counting channel.",
                    color=disnake.Colour(settings.EMBED_COLOR)
                )
                await interaction.send(embed=embed, ephemeral=True)
                return

            db.remove_channel(str(channel.id))
            embed = disnake.Embed(
                title="Channel Removed",
                description=f"Channel <#{channel.id}> successfully removed!",
                color=disnake.Colour(settings.EMBED_COLOR)
            )
            embed.set_footer(text="Your thoughts? Use /feedback to share!")
            await interaction.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error when removing channel: {e}")
            await interaction.send(embed=error.create_error_embed(str(e)), ephemeral=True)


# Add the cog to the bot
def setup(bot):
    bot.add_cog(Disable(bot))
