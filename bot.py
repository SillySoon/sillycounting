import discord
import os
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# Accessing the environment variables
discord_token = os.getenv('DISCORD_TOKEN')


class Bot(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        # Prevent the bot from responding to its own messages
        if message.author == self.user:
            return
        print(f'Message from {message.author}: {message.content}')
        if message.content == 'hello':
            await message.channel.send('Hello!')


intents = discord.Intents.default()
intents.messages = True  # Enable message intent
intents.message_content = True  # This is the privileged intent

client = Bot(intents=intents)
client.run(discord_token)
