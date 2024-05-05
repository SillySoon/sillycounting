# Description: This file contains the eval command which is used to evaluate a number.

# Import the required libraries
from disnake.ext import commands
import disnake
import helper.eval as eval
import settings

# Setup the logger
logger = settings.logging.getLogger('commands')


# This is a test command to check if the bot is working
class Eval(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Command to eval a number
    @commands.slash_command(description='Evaluate a number.')
    async def eval_number(
            self,
            interaction: disnake.ApplicationCommandInteraction,
            expression: str
    ):
        try:
            logger.info(
                f"[{interaction.channel.id}] {interaction.author.id}: /eval_number {expression} ({interaction.id})")

            # Attempt to evaluate the number
            evaluated_number = eval.safe_eval(expression)
            embed = disnake.Embed(
                title="Evaluated Number",
                description=f"Task: `{expression}`\nThe evaluated number is `{evaluated_number}` "
                            f"and will be rounded by the bot to `{round(evaluated_number)}`.",
                color=disnake.Colour(settings.EMBED_COLOR)
            )
            await interaction.send(embed=embed, ephemeral=True)

        except Exception as e:
            # Message that eval doesn't know this number
            embed = disnake.Embed(
                title="Error",
                description=f"Eval doesn't know this number.\n"
                            f"Supported operations: +, -, *, /, **, sin(), cos, tan, log, log10, sqrt, exp, pi, e",
                color=disnake.Colour(settings.EMBED_COLOR)
            )
            await interaction.send(embed=embed, ephemeral=True)


# Add the cog to the bot
def setup(bot):
    bot.add_cog(Eval(bot))
