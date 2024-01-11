import discord
from discord.ext import commands

import logging 
from stats import models
from textwrap import dedent
from timeit import default_timer
from .utils.processor import Processor
from .utils.collector import History_Collector

logger = logging.getLogger('collection')

class Collection_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.processors = dict()
    
    async def get_processor(self, message: discord.Message) -> Processor | None:
        if message.guild.id in self.processors:
            processor = self.processors[message.guild.id]
            if processor.active and not await processor.is_blacklisted(message.author):
                return processor
        return None
    
    @commands.hybrid_command(name="start")
    @commands.check_any(commands.is_owner(), commands.has_guild_permissions(manage_guild=True))
    async def start(self, ctx: commands.Context):
        '''Activate the bot in the guild'''
        if ctx.guild.id in self.processors:
            processor = self.processors[ctx.guild.id]
            await processor.activate()
            await ctx.send("👍")
    
    @commands.hybrid_command(name="history")
    @commands.check_any(commands.is_owner(), commands.has_guild_permissions(manage_guild=True))
    async def history(self, ctx: commands.Context):
        '''Start history collection for a server'''
        if ctx.guild.id in self.processors:
            processor = self.processors[ctx.guild.id]
            if processor.active and not processor.history:
                processor = self.get_processor(ctx.guild)
                self.history_collector = History_Collector(self.bot, ctx.guild, processor)
                self.bot.loop.create_task(self.history_collector.collect_data())
                await ctx.send("👍")

    @commands.hybrid_command(name="stats")
    async def stats(self, ctx: commands.Context):
        '''Get a link to the server's stats page'''
        await ctx.send(f"https://muffinstats.net/guild/{ctx.guild.id}")
    
    @commands.hybrid_command(name="mystats")
    async def mystats(self, ctx: commands.Context):
        '''Get a link to the member's profile'''
        if ctx.author.discriminator == '0':
            tag = ctx.author.name
        else:
            tag = ctx.author.name + '＃' + ctx.author.discriminator
        await ctx.send(f"https://muffinstats.net/guild/{ctx.guild.id}/user/{tag}")


    @commands.Cog.listener()
    async def on_ready(self):
        '''Create a processor instance for the guild'''
        for guild in self.bot.guilds:
            processor = Processor()
            await processor.process_guild(guild)
            self.processors[guild.id] = processor

    @commands.Cog.listener()
    async def on_disconnect(self):
        logger.error("CLIENT DISCONNECTED")
        for processor in self.processors:
            if processor.active:
                await processor.save()
        await self.bot.close()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        '''Create a processor instance for the guild'''
        processor = Processor()
        await processor.process_guild(guild)
        self.processors[guild.id] = processor

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        '''Delete all data associated with the guild'''
        del self.processors[guild.id]
        guild_model_obj = await models.Guild.objects.aget(id=guild.id)
        await guild_model_obj.adelete()
    
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        '''Update the name and/or icon of the guild'''
        processor = self.processors[after.id]
        await processor.process_guild(after)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        '''Create a new channel model object'''
        processor = self.processors[channel.guild.id]
        await processor.process_channel(channel)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        '''Delete all data associated with the channel'''
        channel_model_obj = await models.Channel.objects.aget(id=channel.id)
        await channel_model_obj.adelete()

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after): # unchecked
        '''Update the channel's name'''
        processor = self.processors[after.guild.id]
        await processor.process_channel(after)

    @commands.Cog.listener()
    async def on_member_update(self, before, after): # implementing this isn't really a priority
        pass
    
    @commands.Cog.listener()
    async def on_message(self, message):
        processor = await self.get_processor(message)
        if processor:
            print('processor active')
            processor.process_message(message)

            if processor.cache_count % 20000 == 0:
                self.bot.loop.create_task(self.db_processor.save())



    @commands.Cog.listener()
    async def on_message_edit(self, before, after): 
        processor = await self.get_processor(after)
        if processor:
            processor.process_message(before, unprocess=True)
            processor.process_message(after)


    @commands.Cog.listener()
    async def on_message_delete(self, message): 
        processor = await self.get_processor(message)
        if processor:
            processor.process_message(message, unprocess=True)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, message_list): # unchecked
        if len(message_list) > 0:
            processor = await self.get_processor(message[0])
            if processor:
                for message in message_list:
                    processor.process_message(message, unprocess=True)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        processor = await self.get_processor(reaction.message)
        if processor:
            processor.process_reaction(reaction, 1)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        processor = await self.get_processor(reaction.message)
        if processor:
            processor.process_reaction(reaction, -1)

    @commands.Cog.listener()
    async def on_reaction_clear(self, message, reactions):
        processor = await self.get_processor(message)
        if processor:
            for reaction in reactions:
                processor.process_reaction(reaction, -reaction.count)

    @commands.Cog.listener()
    async def on_reaction_clear_emoji(self, reaction):
        processor = await self.get_processor(reaction.message)
        if processor:
            processor.process_reaction(reaction, -reaction.count)

async def setup(bot):
    await bot.add_cog(Collection_Cog(bot))