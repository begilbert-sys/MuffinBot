import discord
from discord.ext import commands

import logging

from .token import TOKEN


TERMINAL_LOG_LEVEL = logging.INFO


class Stats_Bot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension('.cogs.collection', package = __package__)
        #await self.load_extension('.cogs.interface', package = __package__)


intents = discord.Intents.default()
intents.message_content = True
description = '''A stats bot'''
bot = Stats_Bot(command_prefix='$', description=description, intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

# configure custom logger
logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('debug.log', 'w')
debug_formatter = logging.Formatter('%(name)s - %(levelname)s: %(message)s')
fh.setFormatter(debug_formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

sh = logging.StreamHandler()
terminal_formatter = logging.Formatter('%(message)s')
sh.setFormatter(terminal_formatter)
sh.setLevel(TERMINAL_LOG_LEVEL)
logger.addHandler(sh)

# configure discord logger
discord_logger = logging.getLogger('discord')
dfh = logging.FileHandler('discord.log', 'w')
dfh.setFormatter(debug_formatter)
dfh.setLevel(logging.INFO)
dsh = logging.StreamHandler()
dsh.setFormatter(terminal_formatter)
dsh.setLevel(logging.INFO)
discord_logger.addHandler(dfh)
discord_logger.addHandler(dsh)


def run():
    bot.run(TOKEN)

