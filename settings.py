import os
import logging
from colorlog import ColoredFormatter
from dotenv import load_dotenv
from logging.config import dictConfig
import pathlib

load_dotenv()

# Accessing the environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')
EMBED_COLOR = int(os.getenv('EMBED_COLOR'), 16)
FEEDBACK_CHANNEL_ID = int(os.getenv('FEEDBACK_CHANNEL_ID'))

# Database
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_PORT = os.getenv('DATABASE_PORT')

# Define directories
BASE_DIR = pathlib.Path(__file__).parent
COGS_DIR = BASE_DIR / 'cogs'

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
            '()': 'colorlog.ColoredFormatter',
            'format': "%(log_color)s%(levelname)-10s - %(name)-15s : %(message)s",
            'log_colors': {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'file_bot': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': 'logs/bot.log',
            'mode': 'w',
        },
        'file_user': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': 'logs/user.log',
            'mode': 'w',
        },
    },
    'loggers': {
        'bot': {
            'handlers': ['console', 'file_user'],
            'level': 'INFO',
        },
        'disnake': {
            'handlers': ['console', 'file_bot'],
            'level': 'INFO',
        },
        'database': {
            'handlers': ['console', 'file_bot'],
            'level': 'INFO',
        },
        'commands': {
            'handlers': ['console', 'file_user'],
            'level': 'INFO',
        },
    },
}

dictConfig(LOGGING_CONFIG)
