import discord
from discord.ext import commands

import datetime
import logging 
from stats import models
from textwrap import dedent
from .utils.processor import Processor


logger = logging.getLogger('collection')

class Current_Collection_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_processors = dict()
            
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds: 
            processor = Processor(history=False)
            await processor.process_guild(guild)
            self.active_processors[guild.id] = processor
        print(self.active_processors)
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        processor = Processor()
        await processor.process_guild(guild)
        self.active_processors[guild.id] = processor

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        del self.active_processors[guild.id]
        guild_model_obj = await models.Guild.aget(id=guild.id)
        await guild_model_obj.adelete()
    
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        guild_model_obj = await models.Guild.get(id=after.id)
        guild_model_obj.name = after.name
        guild_model_obj.icon = after.icon
        await guild_model_obj.asave()

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild_model_obj = await models.Guild.aget(id=channel.guild.id)
        channel_model_obj = await models.Channel(
            guild = guild_model_obj,
            id = channel.id,
            name = channel.name
        )
        await channel_model_obj.asave()
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        channel_model_obj = await models.Channel.aget(id=channel.id)
        await channel_model_obj.adelete()

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        channel_model_obj = await models.Channel.get(id=after.id)
        channel_model_obj.name = after.name
        await channel_model_obj.asave()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild_model_obj = await models.Guild.get(id=after.guild.id)
        user_model_obj = await models.User.get(user_id=after.id, guild=guild_model_obj)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        processor = self.active_processors[message.guild.id]

        if message.type is discord.MessageType.reply:
            reply_message = message.reference.resolved
            if type(reply_message) is discord.DeletedReferencedMessage or reply_message is None:
                processor.process_message(message)
            else:
                processor.process_message(message, reply_message)
        else:
            processor.process_message(message)
        
        if processor.cache_count >= 5:
            await processor.save()

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        processor = self.active_processors[after.guild.id]
        processor.process_message(before, unprocess=True)
        processor.process_message(after)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        processor = self.active_processors[message.guild.id]
        processor.process_message(message, unprocess=True)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, message_list):
        assert len(message_list) > 1
        for message in message_list:
            processor = self.active_processors[message_list[0].guild.id]
            processor.process_message(message, unprocess=True)
    
    async def on_reaction_add(self, reaction, user):
        processor = self.active_processors[reaction.message.guild.id]

    async def on_reaction_remove(self, reaction, user):
        pass
    async def on_reaction_clear(self, message, reactions):
        pass
    async def on_reaction_clear_emoji(self, reaction):
        pass

async def setup(bot):
    await bot.add_cog(Current_Collection_Cog(bot))