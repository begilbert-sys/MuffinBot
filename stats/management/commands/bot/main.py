import discord
from discord.ext import commands

from typing import Literal, Optional

import logging
from pathlib import Path

from django.conf import settings

if settings.PRODUCTION_MODE:
    import boto3
    _ssm_client = boto3.client('ssm', 'us-west-1')
    TOKEN = _ssm_client.get_parameter(
        Name=['/discord/token'],
        WithDecryption=True
    )['Parameter']['Value']
else:
    from .token import TOKEN

parentdir = Path(__file__).parent
logging.config.fileConfig(f'{parentdir}/logger.ini')

class Stats_Bot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension('.cogs.collection', package = __package__)


intents = discord.Intents(
    guilds = True,
    members = True,
    guild_messages = True,
    message_content = True,
    emojis = True,
    guild_reactions = True,
)

description = '''A stats bot'''
bot = Stats_Bot(
    command_prefix='$', 
    description=description, 
    intents=intents,
    max_messages = 3000 # extend the message cache 
)


@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    '''
    Sync all bot commands globally 
    '''
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    

def run():
    bot.run(TOKEN)