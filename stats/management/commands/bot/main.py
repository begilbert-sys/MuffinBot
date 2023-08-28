import discord
from discord.ext import commands
import asyncio
import logging

from .presets import TOKEN

from .stats_cog import Processor_Cog
logging.basicConfig(level=logging.INFO, format='%(message)s')

class Stats_Bot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension('.stats_cog', package = __package__)


intents = discord.Intents.default()
intents.message_content = True
description = '''A stats bot'''
bot = Stats_Bot(command_prefix='giveme ', description=description, intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

def run():
    bot.run(TOKEN)

