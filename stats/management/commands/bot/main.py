import discord
from discord.ext import commands

import logging
from pathlib import Path

from .token import TOKEN

parentdir = Path(__file__).parent
logging.config.fileConfig(f'{parentdir}/logger.ini')

class Stats_Bot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension('.cogs.history_collection', package = __package__)
        #await self.load_extension('.cogs.current_collection', package = __package__)
        #await self.load_extension('.cogs.interface', package = __package__)


intents = discord.Intents.default()
intents.message_content = True
description = '''A stats bot'''
bot = Stats_Bot(
    command_prefix='$', 
    description=description, 
    intents=intents,
    max_messages = 3000 # extend the message cache 
)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    

def run():
    bot.run(TOKEN)

