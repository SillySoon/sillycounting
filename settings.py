import os
import logging
from dotenv import load_dotenv
from logging.config import dictConfig

load_dotenv()

# Accessing the environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_PATH = os.getenv('DATABASE_PATH')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')

EMBED_COLOR = int(os.getenv('EMBED_COLOR'), 16)
FEEDBACK_CHANNEL_ID = int(os.getenv('FEEDBACK_CHANNEL_ID'))


# Make sure ./logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        # Add a verbose formatter for debugging with more information
        "verbose": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s",
        },
        # Define the default formatter
        'default': {
            'format': "%(levelname)-10s - %(name)-15s : %(message)s",
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': 'logs/bot.log',
            'mode': 'w',
        },
    },
    'loggers': {
        'bot': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'disnake': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'database': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}

dictConfig(LOGGING_CONFIG)
