import os
from dotenv import load_dotenv

load_dotenv()

# Accessing the environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_PATH = os.getenv('DATABASE_PATH')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')

EMBED_COLOR = int(os.getenv('EMBED_COLOR'), 16)
FEEDBACK_CHANNEL_ID = int(os.getenv('FEEDBACK_CHANNEL_ID'))
