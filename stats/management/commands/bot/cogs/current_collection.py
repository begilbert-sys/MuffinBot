import discord
from discord.ext import commands

import logging 
import pytz
from stats import models
from textwrap import dedent
from utils.processor import get_avatar_id

logger = logging.getLogger('collection')

class Default_Collection_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def timezone(self, ctx, tz_string):
        if tz_string in pytz.all_timezones_set:
            guild_model_obj = await models.Guild.get(id=ctx.guild.id)
            guild_model_obj.timezone = tz_string
            await guild_model_obj.asave()
            ctx.reply('Timezone set')
        else:
            await ctx.reply(dedent(
                f'''{tz_string} is not a valid timezone
                Abbreviated timezones do not work as they aren't specific, or don't consider daylight savings time
                For a list of valid timezones, refer to the \'TZ identifier\' column in the following table: 
                https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List
                '''))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        guild_model_obj = await models.Guild.get(id=guild.id)
        await guild_model_obj.adelete()
    
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        guild_model_obj = await models.Guild.get(id=after.id)
        guild_model_obj.name = after.name
        guild_model_obj.icon = after.icon
        await guild_model_obj.asave()

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        pass
    async def on_guild_channel_update(self, before, after):
        channel_model_obj = await models.Channel.get(id=after.id)
        channel_model_obj.name = after.name
        await channel_model_obj.asave()
    
    async def on_member_update(self, before, after):
        guild_model_obj = await models.Guild.get(id=after.guild.id)
        user_model_obj = await models.User.get(user_id=after.id)
        ###. . . 
    async def on_message(self, message):
        pass