# Description: This file contains the leaderboard command which is used to display the leaderboard of various things.

# Import the required libraries
from disnake.ext import commands
import disnake
import helper.database as db
import helper.error as error
import settings

# Setup the logger
logger = settings.logging.getLogger('commands')


# This is a test command to check if the bot is working
class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # leaderboard command
    @commands.slash_command(description='Show the leaderboard information of various things.')
    async def leaderboard(
            self,
            interaction: disnake.ApplicationCommandInteraction,
            action: str = commands.param(choices=["all servers", "all users", "current channel"]),
    ):
        try:
            logger.info(
                f"[{interaction.channel.id}] {interaction.author.id}: /leaderboard [{action}] ({interaction.id})")

            # Get Top 10 highscore of all channels available in the db
            # Add Emotes to 1st, 2nd, and 3rd place (🥇, 🥈, 🥉)
            if action == "all servers":
                embed = disnake.Embed(
                    title="Server Leaderboard",
                    description="",
                    color=disnake.Colour(settings.EMBED_COLOR)
                )
                for i, (channel_id, highscore) in enumerate(db.get_top_channel_highscores()):
                    bot = self.bot
                    channel = bot.get_channel(int(channel_id))
                    if i == 0:
                        embed.description += f"🥇 {channel.guild.name} - Count: `{highscore}`\n"
                    elif i == 1:
                        embed.description += f"🥈 {channel.guild.name} - Count: `{highscore}`\n"
                    elif i == 2:
                        embed.description += f"🥉 {channel.guild.name} - Count: `{highscore}`\n"
                    else:
                        embed.description += f"**#{i + 1}** {channel.guild.name} - Count: `{highscore}`\n"

                embed.set_footer(text="Your thoughts? Use /feedback to share!")
                await interaction.send(embed=embed, ephemeral=True)

            # Get Top 10 highscore of the current channel
            # Add Emotes to 1st, 2nd, and 3rd place (🥇, 🥈, 🥉)
            elif action == "current channel":
                # Check if channel is a counting channel first
                if not await db.is_channel_allowed(interaction):
                    embed = disnake.Embed(
                        title="Sorry!",
                        description=f"This channel is not activated for counting.",
                        color=disnake.Colour(settings.EMBED_COLOR)
                    )
                    await interaction.send(embed=embed, ephemeral=True)
                    return

                embed = disnake.Embed(
                    title="Channel Leaderboard",
                    description="",
                    color=disnake.Colour(settings.EMBED_COLOR)
                )
                for i, (user_id, count) in enumerate(db.get_top_user_highscores(channel_id=interaction.channel.id)):
                    if i == 0:
                        embed.description += f"🥇 <@{user_id}> - Count: `{count}`\n"
                    elif i == 1:
                        embed.description += f"🥈 <@{user_id}> - Count: `{count}`\n"
                    elif i == 2:
                        embed.description += f"🥉 <@{user_id}> - Count: `{count}`\n"
                    else:
                        embed.description += f"**#{i + 1}** <@{user_id}> - Count: `{count}`\n"

                embed.set_footer(text="Your thoughts? Use /feedback to share!")
                await interaction.send(embed=embed, ephemeral=True)

            # Get Top 10 highscore of all users : get_top_users()
            # Add Emotes to 1st, 2nd, and 3rd place (🥇, 🥈, 🥉)
            elif action == "all users":
                embed = disnake.Embed(
                    title="User Leaderboard",
                    description="",
                    color=disnake.Colour(settings.EMBED_COLOR)
                )
                for i, (user_id, count) in enumerate(db.get_top_users()):
                    if i == 0:
                        embed.description += f"🥇 <@{user_id}> - Count: `{count}`\n"
                    elif i == 1:
                        embed.description += f"🥈 <@{user_id}> - Count: `{count}`\n"
                    elif i == 2:
                        embed.description += f"🥉 <@{user_id}> - Count: `{count}`\n"
                    else:
                        embed.description += f"**#{i + 1}** <@{user_id}> - Count: `{count}`\n"

                embed.set_footer(text="Your thoughts? Use /feedback to share!")
                await interaction.send(embed=embed, ephemeral=True)

        # Catch any exceptions and send an error message
        except Exception as e:
            logger.error(f"Error when getting highscore: {e}")
            await interaction.send(embed=error.create_error_embed(str(e)), ephemeral=True)


# Add the cog to the bot
def setup(bot):
    bot.add_cog(Leaderboard(bot))
