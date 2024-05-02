import disnake
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Accessing the environment variables
embed_color = int(os.getenv('EMBED_COLOR'), 16)


def create_error_embed(error: str):
    error_message = ("There was an error while executing this command!"
                     "\nJoin the Support Server and send us the error message:"
                     f"\n```\n{error}```"
                     f"\nhttps://discord.gg/G6xppCptWF")
    embed = disnake.Embed(title="Command Error", description=error_message, color=disnake.Colour(embed_color))
    return embed
