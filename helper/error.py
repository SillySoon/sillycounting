import disnake
import settings


def create_error_embed(error: str):
    error_message = ("There was an error while executing this command!"
                     "\nJoin the Support Server and send us the error message:"
                     f"\n```\n{error}```"
                     f"\nhttps://discord.gg/G6xppCptWF")
    embed = disnake.Embed(title="Command Error", description=error_message, color=disnake.Colour(settings.EMBED_COLOR))
    return embed
